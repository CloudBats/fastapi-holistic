import os
from pathlib import Path

from invoke import task


PIP_ARGS = "--disable-pip-version-check --no-cache-dir"
PIP_COMMAND = f"pip {PIP_ARGS}"
VENV_DIR = os.getenv("VENV_DIR", ".venv")
# Do NOT use /usr/bin/python3 for the official Python docker image, it doesn't touch the system python found there
# TODO: this only works in the official Python docker image, use /usr/bin/python3 if /usr/local/bin/python3 is missing
SYSTEM_PYTHON_PATH = "/usr/local/bin/python3"
cwd = Path.cwd()


# TODO: see if this is better as an attribute instead of a function
def get_wheel_path():
    for path in (cwd / "dist").iterdir():
        if path.name.endswith(".whl"):
            return path

    return None


# =====
# BUILD
# =====


@task
def clean_dist(c):
    """Cleans dist artifacts."""
    # TODO add pycache cleanup
    c.run("rm -rf dist")


@task(clean_dist)
def build(c):
    """Create wheel. Cleans first."""
    c.run("poetry build --format wheel -vv")


# create requirements wheels
# pip wheel -r requirements.txt
# install requirements wheels
# ${VENV_DIR}/bin/pip install *.whl


# ============
# DEPENDENCIES
# ============


@task
def requirements_lock_build(c):
    """Create lock file. Intended for use before committing."""
    c.run("poetry lock --no-update")


# TODO: see if hashes should be included
@task
def requirements_build(c):
    """Exports requirements.txt using Poetry. Intended for venv caching."""
    c.run("poetry export --format requirements.txt --output requirements.txt --without-hashes")


# TODO: see if hashes should be included
@task
def requirements_build_dev(c):
    """Exports dev requirements.txt using Poetry. Intended for venv caching."""
    c.run("poetry export --dev --format requirements.txt --output requirements.txt --without-hashes")


# =======
# INSTALL
# =======


@task
def clean_local_venv(c):
    c.run(f"rm -rf {VENV_DIR}")


@task
def requirements_install_local_venv(c):
    """Installs dependencies using pip in local venv."""
    c.run(f"{VENV_DIR}/bin/{PIP_COMMAND} install -r requirements.txt")


@task
def requirements_install(c):
    """Installs dependencies using pip in active venv (WARNING: pollutes system python if no active venv)."""
    c.run(f"{PIP_COMMAND} install -r requirements.txt")


@task(build, post=[clean_dist])
def app_install_local_venv_no_deps(c):
    """Installs app without dependencies using pip in local venv.
    It's important to install without dependencies to avoid pip dependency resolution in favor of poetry."""
    c.run(f"{VENV_DIR}/bin/{PIP_COMMAND} install --no-deps {get_wheel_path()}")


@task(build, post=[clean_dist])
def app_install_no_deps(c):
    """Installs app without dependencies using pip in active venv (WARNING: pollutes system python if no active venv).
    It's important to install without dependencies to avoid pip dependency resolution in favor of poetry.
    """
    c.run(f"{PIP_COMMAND} install --no-deps {get_wheel_path()}")


@task(requirements_install_local_venv, app_install_local_venv_no_deps)
def install_local_venv(c):
    """Installs dependencies, then the app using pip in local venv."""


@task(requirements_install, app_install_no_deps)
def install(c):
    """Installs dependencies, then the app using pip in active venv (WARNING: pollutes system python if no active venv)."""


# TODO: find a better way than activate
@task(build)
def install_dev_local_venv(c):
    """Installs app in develop/editable mode and main+dev dependencies using Poetry in local venv."""
    c.run(f". {VENV_DIR}/bin/activate && poetry install")


@task(build)
def install_dev(c):
    """Installs app in develop/editable mode and main+dev dependencies using Poetry in active venv (WARNING: pollutes system python if no active venv)."""
    c.run("poetry install")


# ============
# POETRY SETUP
# ============


@task
def poetry_config_venv_create_in_project(c):
    """Configures poetry to create virtual env in the project dir by default.

    https://python-poetry.org/docs/configuration/#virtualenvsin-project"""

    c.run("poetry config --local virtualenvs.in-project true")


@task
def poetry_config_venv_no_create(c):
    """Configures poetry to not create a virtual env by default.

    https://python-poetry.org/docs/configuration/#virtualenvscreate"""

    c.run("poetry config --local virtualenvs.create false")


@task(poetry_config_venv_create_in_project, poetry_config_venv_no_create)
def poetry_configure(c):
    pass


POETRY_VERSION = "1.1.13"


# intended for dev env
# TODO: check supported python versions
@task(post=[poetry_configure])
def poetry_install_system(c):
    c.run(f"curl -sS -L https://install.python-poetry.org | {SYSTEM_PYTHON_PATH} - --version {POETRY_VERSION} --force")


# intended for server or container env, uses system python version, only for generating requirements.txt
# TODO: check supported python versions
@task(post=[poetry_configure])
def poetry_install_pipx(c):
    c.run(f'pipx install --pip-args "{PIP_ARGS}" "poetry~={POETRY_VERSION}"')


@task
def poetry_use_local_venv(c):
    c.run(f"poetry env use {VENV_DIR}/bin/python")


# ==========
# VENV SETUP
# ==========

@task
def venv_install_build_tools(c):
    """Add proper, stable build tool versions to virtual env."""
    c.run(f"{VENV_DIR}/bin/python -m {PIP_COMMAND} install -r requirements-build.txt")


@task(post=[venv_install_build_tools])
def venv_create_system(c):
    c.run(f"{SYSTEM_PYTHON_PATH} -m venv {VENV_DIR}")


# TODO: get these from the environment
PYTHON_VERSION = "3.10.5"
PROJECT_NAME = "fastapi-holistic"
PYENV_VENV_NAME = f"{PROJECT_NAME}-{PYTHON_VERSION.replace('.', '')}"


@task
def pyenv_check(c):
    c.run(
        'if ! pyenv --version ;'
        ' then echo "Missing pyenv, see: https://github.com/pyenv/pyenv#installation" && exit 1;'
        ' fi'
    )


@task(pyenv_check)
def python_install_pyenv(c, python_version=PYTHON_VERSION):
    c.run(f"pyenv install {python_version}")


@task(pre=[python_install_pyenv], post=[venv_install_build_tools])
def venv_create_pyenv(c, python_version=PYTHON_VERSION, venv_name=PYENV_VENV_NAME):
    c.run(f"pyenv virtualenv {python_version} {venv_name}")
    c.run(f"pyenv local {venv_name}")
