from invoke import task

from . import config
from . import _utils
from . import requirements


@task
def clean_dist(c):
    """Cleans dist artifacts."""
    # TODO add pycache cleanup
    c.run("rm -rf dist")


@task(clean_dist)
def build(c):
    """Create wheel. Cleans first."""
    c.run("poetry build --format wheel -vv")


@task(build, post=[clean_dist])
def install_in_local_venv_no_deps(c):
    """Installs app without dependencies using pip in local venv.
    It's important to install without dependencies to avoid pip dependency resolution in favor of poetry."""
    pip_install_command = config.pip_install_command(interpreter="local")
    c.run(f"{pip_install_command} --no-deps {_utils.get_wheel_path()}")


@task(build, post=[clean_dist])
def install_in_active_venv_no_deps(c):
    """Installs app without dependencies using pip in active venv (WARNING: pollutes system python if no active venv).
    It's important to install without dependencies to avoid pip dependency resolution in favor of poetry."""
    pip_install_command = config.pip_install_command(interpreter="active")
    c.run(f"{pip_install_command} --no-deps {_utils.get_wheel_path()}")


@task(requirements.install_in_local_venv, install_in_local_venv_no_deps)
def install_in_local_venv(c):
    """Installs dependencies, then the app using pip in local venv."""


@task(requirements.install_in_active_venv, install_in_active_venv_no_deps)
def install_in_active_venv(c):
    """Installs dependencies, then the app using pip in active venv (WARNING: pollutes system python if no active venv)."""


# TODO: find a better way than activate, simply running poetry install worked at some point
@task(build)
def install_dev_in_local_venv(c):
    """Installs app in develop/editable mode and main+dev dependencies using Poetry in local venv."""
    c.run(f". {config.VENV_DIR}/bin/activate && poetry install --no-interaction")


# TODO: check for active venv via VIRTUAL_ENV env var
@task(build)
def install_dev_in_active_venv(c):
    """Installs app in develop/editable mode and main+dev dependencies using Poetry in active venv (WARNING: pollutes system python if no active venv)."""
    c.run("poetry install --no-interaction")
