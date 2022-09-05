# TODO: use ARG to supply image names
ARG VENV_DIR=.venv
ARG APP_USER=app
ARG PYTHON_VERSION=3.10

# Using full image for building, as it includes many libs required for compilation
FROM python:${PYTHON_VERSION} AS build-base-python3
COPY config/tools/pip.conf /etc/
#RUN apt update
#RUN apt install -y python3-venv
# TODO: figure out a way to install python3.10-venv instead of python3.9-venv
#ARG PYTHON_VERSION
#RUN apt install -y python${PYTHON_VERSION}-venv

ARG APP_USER
RUN groupadd -r ${APP_USER} && useradd --no-log-init --system --create-home -g ${APP_USER} ${APP_USER}
USER ${APP_USER}
ENV PATH="/home/${APP_USER}/.local/bin:${PATH}"

WORKDIR /home/${APP_USER}
# Copy tasks in root only for bootstrapping, separate from app
COPY Makefile ./
#RUN make pip-install-system
RUN make pipx-install
RUN make invoke-install-pipx
COPY tasks/ tasks/
RUN invoke bootstrap.poetry

WORKDIR ./app


# Using small image for production
FROM python:${PYTHON_VERSION}-slim AS base-python3

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random
COPY config/tools/pip.conf /etc/
RUN apt update
RUN apt install -y make
#RUN apt install -y curl python3-venv
# TODO: figure out a way to install python3.10-venv instead of python3.9-venv
#ARG PYTHON_VERSION
#RUN apt install -y python${PYTHON_VERSION}-venv

ARG APP_USER
RUN groupadd -r ${APP_USER} && useradd --no-log-init --system --create-home -g ${APP_USER} ${APP_USER}
USER ${APP_USER}
ENV PATH="/home/${APP_USER}/.local/bin:${PATH}"

WORKDIR /home/${APP_USER}
COPY Makefile ./
#RUN make pip-install-system
RUN make pipx-install
RUN make invoke-install-pipx

WORKDIR ./app


FROM build-base-python3 AS build

ARG VENV_DIR
# Invalidates layer cache on dependency version changes
COPY tasks/ tasks/
COPY pyproject.toml poetry.lock requirements-build.txt ./
RUN invoke bootstrap.venv-local
RUN invoke prod.requirements-build
# Install dependencies as dedicated layer
RUN invoke prod.requirements-install
# Invalidates layer cache on app source changes
COPY src/ src/
# Install app as dedicated layer
RUN invoke prod.install-local-venv


FROM build-base-python3 AS build-dev

ARG VENV_DIR
# Invalidates layer cache on dependency version changes
COPY tasks/ tasks/
COPY pyproject.toml poetry.lock requirements-build.txt ./
RUN invoke bootstrap.venv-local
RUN invoke dev.requirements-build
# Install dependencies as dedicated layer
RUN invoke dev.requirements-install
# Invalidates layer cache on app source changes
COPY src/ src/
# Install app as dedicated layer
RUN invoke dev.install-local-venv

# TODO: consider using pip install --install-option="--prefix=/install"
#       and avoid the ${VENV_DIR} altogether, but then poetry must be installed separately


FROM base-python3 AS app

COPY tasks/ tasks/
ARG APP_USER
ARG VENV_DIR
COPY --from=build /home/${APP_USER}/app/${VENV_DIR} ${VENV_DIR}/
COPY scripts/gunicorn_conf.py scripts/gunicorn_conf.py

ENV PORT=8080
EXPOSE ${PORT}

CMD ["invoke", "prod.start"]


FROM base-python3 AS app-dev-base

COPY tasks/ tasks/
ARG APP_USER
ARG VENV_DIR
COPY --from=build-dev /home/${APP_USER}/app/${VENV_DIR} ${VENV_DIR}/
COPY scripts/gunicorn_conf.py scripts/gunicorn_conf.py
COPY .env-local-defaults ./

ENV PORT=8080
EXPOSE ${PORT}


# We expect src/, config/ and tests/ to be volume mounts
FROM app-dev-base AS app-dev

CMD ["invoke", "dev.start"]


FROM app-dev-base AS app-ci

COPY src/ src/
COPY config/ config/
COPY tests/ tests/

CMD ["invoke", "ci.test"]
