from invoke import task

from . import config


# TODO: check for requirements-build.txt and emit error if it's missing
@task
def install_build_tools_local(c):
    """Add proper, stable build tool versions to virtual env."""
    pip_install_command = config.pip_install_command(interpreter="local")
    c.run(f"{pip_install_command} -r requirements-build.txt")


@task(post=[install_build_tools_local])
def create_with_system(c):
    """Crete a virtual env using the system Python interpreter."""
    c.run(f"{config.SYSTEM_PYTHON_PATH} -m venv {config.VENV_DIR}")


@task
def clean_local(c):
    c.run(f"rm -rf {config.VENV_DIR}")
