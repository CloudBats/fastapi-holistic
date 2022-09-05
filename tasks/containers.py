from contextlib import contextmanager
from typing import Optional

from invoke import task

from . import packaging
from . import utils
from . import run

DOCKER_ENV = dict(DOCKER_BUILDKIT="1", BUILDKIT_PROGRESS="plain")

APP_USER = "app"
APP_IMAGE_NAME_PROD = "app"
APP_IMAGE_NAME_DEV = "app-dev"
APP_CONTAINER_NAME_PROD = APP_IMAGE_NAME_PROD
APP_CONTAINER_NAME_DEV = APP_IMAGE_NAME_DEV


def format_docker_env_options(variables: Optional[dict] = None, file_name: Optional[str] = None):
    env_options = "".join(f" --env {k}={v}" for k, v in variables.items()) if variables else ""
    env_file_option = f" --env-file {file_name}" if file_name and (utils.cwd / file_name).is_file() else ""

    return env_options + env_file_option


DOCKER_VOLUME_MOUNTS = (
    f" --mount type=bind,src={utils.cwd}/src,dst=/home/{APP_USER}/app/src"
    f" --mount type=bind,src={utils.cwd}/config,dst=/home/{APP_USER}/app/config"
    f" --mount type=bind,src={utils.cwd}/tests,dst=/home/{APP_USER}/app/tests"
)
DOCKER_DEV_RUN_COMMAND = (
    "docker run -d"
    f"{format_docker_env_options(file_name=utils.DOT_ENV_FILE_NAME)}"
    " --network host"
    f"{DOCKER_VOLUME_MOUNTS}"
    f" --name {APP_CONTAINER_NAME_DEV}"
    f" {APP_IMAGE_NAME_DEV}"
    " /usr/bin/tail -f /dev/null"
)
DOCKER_LINT_COMMAND = (
    "docker exec -it"
    f" {APP_CONTAINER_NAME_DEV}"
    # TODO:  create invoke task for venv related commands
    f" /bin/bash -c '. {packaging.VENV_DIR}/bin/activate && invoke dev.lint'"
)
DOCKER_TEST_COMMAND = (
    "docker exec -it"
    f" {APP_CONTAINER_NAME_DEV}"
    f" /bin/bash -c '. {packaging.VENV_DIR}/bin/activate && invoke dev.pytest'"
)


@task
def docker_build_base_images(c):
    # TODO: fix targets and tags
    c.run("docker build --tag build-base-python3 --target=build-base-python3 .", env=DOCKER_ENV)
    c.run("docker build --tag base-python3 --target=base-python3 .", env=DOCKER_ENV)


@task(packaging.requirements_build, docker_build_base_images)
def docker_build(c):
    c.run(f"docker build --tag {APP_IMAGE_NAME_PROD} --target=app .", env=DOCKER_ENV)


@task(packaging.requirements_build_dev, docker_build_base_images)
def docker_build_dev(c):
    c.run(f"docker build --tag {APP_IMAGE_NAME_DEV} --target=app-dev .", env=DOCKER_ENV)


DB_IMAGE_NAME = "postgres:12"
DB_CONTAINER_NAME = "app-db"
DB_PORT = "5432"


@task
def start_db_docker(c):
    import os

    utils.load_dotenv_in_env()
    db_vars = {
        k: os.getenv(k, utils.get_env_local_defaults().get(k))
        for k in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")
    }
    c.run(
        "docker run -d"
        f" --publish {run.HOST}:{DB_PORT}:{DB_PORT}"
        f"{format_docker_env_options(db_vars)}"
        # f" --mount type=bind,src={cwd}/config,dst=/app/config"
        f" --name {DB_CONTAINER_NAME}"
        f" {DB_IMAGE_NAME}"
    )
    # TODO: look into persistence options for more advanced dev use
    #     volumes:
    #       - app-db-data:/var/lib/postgresql/data/pgdata
    #     volumes:
    #   app-db-data:


# TODO: see how to replace this with @task parameters
def stop_rm_docker_container(c, container_name: str):
    c.run(f"echo Attempting to stop and remove {container_name} docker container...", echo=False)
    result = c.run(f"docker container ls -a -q --filter name={container_name}").stdout.strip()
    if result:
        c.run(f"docker container stop {result}")
        c.run(f"docker container rm {result}")
    else:
        c.run(f"echo Docker container not found, moving on.", echo=False)


@task
def stop_rm_db_docker(c):
    stop_rm_docker_container(c, DB_CONTAINER_NAME)


@task(stop_rm_db_docker, start_db_docker)
def restart_db_docker(c):
    pass


@contextmanager
def db_docker(c):
    stop_rm_db_docker(c)
    start_db_docker(c)
    # TODO: implement a better mechanism to check for DB being responsive
    import time

    time.sleep(5)
    try:
        yield
    finally:
        stop_rm_db_docker(c)


# =======
# APP RUN
# =======


@task
def stop_app_prod_docker(c):
    stop_rm_docker_container(c, APP_CONTAINER_NAME_PROD)


@contextmanager
def app_prod_docker_cleanup(c):
    stop_app_prod_docker(c)
    try:
        yield
    finally:
        stop_app_prod_docker(c)


@task(docker_build)
def start_app_prod_docker(c):
    """Starts a prod app container. Doesn't create a DB container."""
    with app_prod_docker_cleanup(c):
        c.run(
            "docker run -it"
            " --network host"
            f" --publish {run.HOST}:{run.PORT}:{run.PORT}"
            f"{format_docker_env_options(utils.get_env_local_defaults())}"
            f" --name {APP_CONTAINER_NAME_PROD}"
            f" {APP_IMAGE_NAME_PROD}"
        )
        # LD_LIBRARY_PATH is a ridiculous fix for a gcloud-induced crash
        # https://github.com/google-github-actions/setup-gcloud/issues/128
        # https://github.com/docker/compose/issues/5930
        # c.run("LD_LIBRARY_PATH=/usr/local/lib COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up app")


@task(docker_build)
def start_app_prod_docker_with_db_docker(c):
    """Starts an app container after creating a DB container."""
    with db_docker(c):
        start_app_prod_docker(c)


@task
def stop_dev_docker(c):
    stop_rm_docker_container(c, APP_CONTAINER_NAME_DEV)


@contextmanager
def app_dev_docker_cleanup(c):
    stop_dev_docker(c)
    try:
        yield
    finally:
        stop_dev_docker(c)


@task(docker_build_dev)
def start_dev_docker(c):
    """Starts a dev app container. Doesn't create a DB container."""
    with app_dev_docker_cleanup(c):
        c.run(
            "docker run -it"
            " --network host"
            # f" --publish {run.HOST}:{run.PORT}:{run.PORT}"
            f"{format_docker_env_options(file_name=utils.DOT_ENV_FILE_NAME)}"
            f"{DOCKER_VOLUME_MOUNTS}"
            f" --name {APP_CONTAINER_NAME_DEV}"
            f" {APP_IMAGE_NAME_DEV}"
        )


# TODO: see how to inherit docker_build_dev when running task as function instead of pre/post
@task(docker_build_dev)
def start_dev_docker_with_db_docker(c):
    """Starts an app container after creating a DB container."""
    with db_docker(c):
        start_dev_docker(c)
