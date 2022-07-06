from invoke import task

from . import containers

# TODO: add shell and yaml linters


TOOLS_CONFIG_PATH = "config/tools"
SOURCES_PATH = "src"
TESTS_PATH = "tests"


@task
def pylint(c):
    c.run(f"pylint {SOURCES_PATH} --rcfile {TOOLS_CONFIG_PATH}/pylintrc")


@task
def flake8(c):
    c.run(f"flake8 {SOURCES_PATH} --config {TOOLS_CONFIG_PATH}/.flake8")


@task
def autoflake(c):
    c.run(
        f"autoflake {SOURCES_PATH}"
        " --recursive --in-place --remove-all-unused-imports --ignore-init-module-imports"
        " --remove-duplicate-keys --remove-unused-variables",
        warn=True,
    )


@task
def black_apply(c):
    c.run(f"black {SOURCES_PATH} {TESTS_PATH} --config {TOOLS_CONFIG_PATH}/black.toml", warn=True)


@task
def black_check(c):
    c.run(f"black {SOURCES_PATH} {TESTS_PATH} --config {TOOLS_CONFIG_PATH}/black.toml --check")


@task
def isort_apply(c):
    c.run(f"isort {SOURCES_PATH} {TESTS_PATH} --sp {TOOLS_CONFIG_PATH}/.isort.cfg", warn=True)


@task
def isort_check(c):
    c.run(f"isort {SOURCES_PATH} {TESTS_PATH} --sp {TOOLS_CONFIG_PATH}/.isort.cfg --check-only")


@task
def mypy(c):
    c.run(f"mypy --config-file {TOOLS_CONFIG_PATH}/mypy.ini")


@task
def pytest(c, path=TESTS_PATH, environment="test", record=False):
    """Runs all the tests with pytest. Use the record option to control VCR.

    To set up in PyCharm, configure the following in your pytest template:
    - working directory to the repository root to avoid it being set to the directory of the currently running test(s)
    - add ENVIRONMENT=test in environment variables
    - add the following to additional arguments:
      -c {TOOLS_CONFIG_PATH}/pytest.ini --cov-config {TOOLS_CONFIG_PATH}/.coveragerc --record-mode none --block-network
      For example:
      -c config/tools/pytest.ini --cov-config config/tools/.coveragerc --record-mode none --block-network
    """
    env = dict(ENVIRONMENT=environment)
    record_option = "--record-mode once" if record else "--record-mode none --block-network"
    c.run(
        f"pytest {path} -c {TOOLS_CONFIG_PATH}/pytest.ini --cov-config {TOOLS_CONFIG_PATH}/.coveragerc {record_option}",
        env=env,
    )


MIGRATIONS_COMMAND = "app-db-migrations upgrade-head"


@task
def pytest_with_migrations(c, path=TESTS_PATH, environment="test", record=False):
    c.run(MIGRATIONS_COMMAND)
    pytest(c, path, environment, record)


@task
def pytest_with_docker_db(c):
    """Runs tests creating a DB container for the duration of the run."""

    with containers.db_docker(c):
        # TODO: replace with task
        c.run(". ./scripts/prestart.sh")
        pytest(c)


@task(autoflake, black_apply, isort_apply, name="format")
def format_(c):
    """Run all format tasks. Modifies non-conforming files."""


@task(black_check, isort_check, flake8, pylint)
def lint(c):
    """Run all lint checks."""


# TODO: create alternative for running without docker
@task(lint, pytest_with_migrations)
def test_ci(c):
    """Run all lint checks and unit tests. Targets CI."""


@task(format_, test_ci)
def test_dev(c):
    """Runs formatting and then all lint checks and unit tests. Targets local development."""


@task(format_, containers.docker_build_dev)
def test_dev_with_db_docker(c):
    with containers.app_dev_docker_cleanup(c):
        c.run(containers.DOCKER_DEV_RUN_COMMAND)
        c.run(containers.DOCKER_LINT_COMMAND)
        with containers.db_docker(c):
            # TODO: replace with task
            c.run(". ./scripts/prestart.sh")
            c.run(containers.DOCKER_TEST_COMMAND)
