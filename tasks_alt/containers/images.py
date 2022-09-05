from invoke import task

from .. import config
from ..containers import docker_utils
from .. import requirements

BUILD_ENV = dict(DOCKER_BUILDKIT="1", BUILDKIT_PROGRESS="plain")
BUILD_ARGS = dict(
    APP_USER=config.APP_USER,
    VENV_DIR=config.VENV_DIR,
    APP_USER_ID=config.APP_USER_ID,
    APP_GROUP_ID=config.APP_GROUP_ID,
    **requirements.build_download_extras_env(venv="local"),
)

PYTHON_BASE_IMAGE_NAME = "app-python"
APP_BASE_IMAGE_NAME = "app-base"
APP_BUILD_BASE_IMAGE_NAME = "app-build-base"
APP_IMAGE_NAME_PROD = "app"
APP_IMAGE_NAME_DEV = "app-dev"


@task
def build_bases(c):
    for image in PYTHON_BASE_IMAGE_NAME, APP_BASE_IMAGE_NAME, APP_BUILD_BASE_IMAGE_NAME:
        c.run(docker_utils.format_build_command(image, args=BUILD_ARGS), env=BUILD_ENV)


@task
def build_app(c):
    c.run(docker_utils.format_build_command(APP_IMAGE_NAME_PROD, args=BUILD_ARGS), env=BUILD_ENV)


@task
def build_app_dev(c):
    c.run(docker_utils.format_build_command(APP_IMAGE_NAME_DEV, args=BUILD_ARGS), env=BUILD_ENV)
