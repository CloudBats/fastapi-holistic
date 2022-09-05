from invoke import task

from .. import config
from .docker_utils import Service, Volume


service = Service(
    image_name=config.APP_IMAGE_NAME,
    container_name=config.APP_CONTAINER_NAME,
    volumes=[
        Volume(source_relative="src", destination_absolute=f"/home/{config.APP_USER}/src"),
        Volume(source_relative="tasks", destination_absolute=f"/home/{config.APP_USER}/tasks"),
    ],
    user=f"{config.APP_USER_ID}:{config.APP_GROUP_ID}",
    exposed_ports=[config.APP_PORT],
    published_ports=[config.APP_PORT],
)


@task
def initial_migrations_local(c):
    c.run(service.format_run_with_custom_command_script("invoke migrations.run-all"))


@task
def test(c):
    c.run(service.format_run_with_custom_command_script("invoke dev.app.test"))
