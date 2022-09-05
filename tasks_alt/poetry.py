from invoke import task

from . import config


@task
def config_venv_create_in_project(c):
    """Configures poetry to create virtual env in the project dir by default.

    https://python-poetry.org/docs/configuration/#virtualenvsin-project"""

    c.run("poetry config --local virtualenvs.in-project true")


@task
def config_venv_no_create(c):
    """Configures poetry to not create a virtual env by default.

    https://python-poetry.org/docs/configuration/#virtualenvscreate"""

    c.run("poetry config --local virtualenvs.create false")


@task(config_venv_create_in_project, config_venv_no_create)
def configure(c):
    pass


@task(post=[configure])
def install_with_pipx(c):
    c.run(f'pipx install --pip-args "{config.pip_args()}" "poetry~={config.POETRY_VERSION}"')
