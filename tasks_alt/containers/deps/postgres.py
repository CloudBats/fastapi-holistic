from invoke import task

from ..docker_utils import Volume, Service

service = Service(
    image_name="bitnami/postgresql",
    image_tag="13",
    container_name="postgres",
    environment=dict(
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="postgres",
        POSTGRES_DB="local",
    ),
    published_ports=[5432],
)


@task
def test(c):
    c.run("NOT IMPLEMENTED YET")


@task
def client(c):
    c.run("NOT IMPLEMENTED YET")


@task
def client_docker(c):
    c.run("NOT IMPLEMENTED YET")
