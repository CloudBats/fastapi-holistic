from invoke import task

from . import config


@task
def lock_build(c):
    """Create lock file. Intended for use before committing."""
    c.run("poetry lock --no-update")


# TODO: see if hashes should be included
@task
def build(c):
    """Exports requirements.txt using Poetry. Intended for venv caching."""
    c.run(f"poetry export --format requirements.txt --output {config.REQUIREMENTS_FILE} --without-hashes")


# TODO: see if hashes should be included
@task
def build_dev(c):
    """Exports dev requirements.txt using Poetry. Intended for venv caching."""
    c.run(f"poetry export --dev --format requirements.txt --output {config.REQUIREMENTS_FILE} --without-hashes")


# TODO: try poetry install --no-root --no-dev
@task
def install_in_local_venv(c, cache_dir=""):
    # TODO: check paths exist
    """Installs dependencies using pip in local venv."""
    pip_install_command = config.pip_install_command(interpreter="local", cache_dir=cache_dir)
    c.run(f"{pip_install_command} -r {config.REQUIREMENTS_FILE}")


# TODO: check VIRTUAL_ENV env var is set
# TODO: see about using an alternative: poetry install --no-root
@task
def install_in_active_venv(c):
    """Installs dependencies using pip in active venv (WARNING: pollutes system python if no active venv)."""
    pip_install_command = config.pip_install_command(interpreter="active")
    c.run(f"{pip_install_command} -r {config.REQUIREMENTS_FILE}")
