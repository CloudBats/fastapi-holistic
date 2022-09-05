from invoke import Collection

from . import poetry
from . import venv
from . import app
from . import requirements
from . import containers
from .containers import images as container_images
from .containers import app as container_app
from .containers import deps as container_deps
from .containers import networks as container_networks

ns = Collection(
    poetry=Collection(
        poetry.install_with_pipx,
    ),
    venv=Collection(
        venv.create_with_system,
        # TODO: add venv.create_with_pyenv
    ),
    dev=Collection(
        reqs=Collection(
            install_local_venv=requirements.install_in_local_venv,
            install_active_venv=requirements.install_in_active_venv,
            build=requirements.build_dev,
        ),
        app=Collection(
            install_local_venv=app.install_dev_in_local_venv,
        ),
    ),
    prod=Collection(
        reqs=Collection(
            install_local_venv=requirements.install_in_local_venv,
            build=requirements.build_dev,
        ),
        app=Collection(
            install_local_venv=app.install_in_local_venv_no_deps,
        ),
    ),
    migrations=Collection(
    ),
    docker=Collection(
        containers.system_all_down,
        images=Collection(
            # TODO: add test and push tasks
            base=Collection(
                build_all=container_images.build_bases,
            ),
            app=Collection(
                build_prod=container_images.build_app,
                build_dev=container_images.build_app_dev,
            ),
        ),
        networks=Collection(
            app=Collection(
                up=container_networks.app_up,
                down=container_networks.app_down,
            )
        ),
        dev=Collection(
            containers.local_all_up,
            containers.local_all_down,
            containers.local_test_clean,
            app=Collection(
                *container_app.service.all_tasks,
                container_app.test,
            ),
            migrations=Collection(
                container_app.initial_migrations_local,
            ),
            deps=Collection(
                container_deps.all_up,
                container_deps.all_down,
            ),
        ),
        prod=Collection(
            docker=Collection(
            ),
        ),
    ),
)
