"""Task management

For shell tab completions:
http://docs.pyinvoke.org/en/stable/invoke.html#shell-tab-completion
Examples:
source <(inv --print-completion-script zsh)
inv --print-completion-script zsh > ~/.invoke-completion.sh
"""

from invoke import Collection

from . import containers
from . import run
from . import validation
from . import packaging
from . import benchmarks
from . import utils


db_collection = Collection(
    start=containers.start_db_docker, stop=containers.stop_db_docker, restart=containers.restart_db_docker
)
ns = Collection(
    bootstrap=Collection(
        poetry=packaging.poetry_install_pipx,
        venv_local=packaging.venv_create_system,
        venv_pyenv=packaging.venv_create_pyenv,
    ),
    dev=Collection(
        validation.format_,
        utils.curlme,
        requirements_build=packaging.requirements_build_dev,
        requirements_lock=packaging.requirements_lock_build,
        requirements_install=packaging.requirements_install_local_venv,
        install=packaging.install_dev,
        install_local_venv=packaging.install_dev_local_venv,
        start=run.start_uvicorn_dev,
        start_gunicorn=run.start_gunicorn_dev,
        lint=validation.lint,
        pytest=validation.pytest,
        test=validation.test_dev,
        benchme=benchmarks.benchmark_ab_docker,
        docker=Collection(
            db=db_collection,
            build=containers.docker_build_dev,
            start=containers.start_dev_docker_with_db_docker,
            stop=containers.stop_dev_docker,
            test=validation.test_dev_with_db_docker,
            pytest=validation.pytest_with_docker_db,
        ),
    ),
    prod=Collection(
        packaging.requirements_build,
        packaging.clean_dist,
        packaging.build,
        packaging.app_install_local_venv_no_deps,
        requirements_install=packaging.requirements_install_local_venv,
        install=packaging.install,
        install_local_venv=packaging.install_local_venv,
        start=run.start_gunicorn,
        docker=Collection(
            db=db_collection,
            build=containers.docker_build,
            start=containers.start_prod_docker_with_db_docker,
            stop=containers.stop_prod_docker,
        ),
    ),
    ci=Collection(
        requirements_build=packaging.requirements_build_dev,
        test=validation.test_ci,
    ),
)
# TODO: see if tasks.dedupe helps with running a clean task both pre and post
ns.configure(dict(run=dict(pty=True, echo=True), tasks=dict(dedupe=False)))
