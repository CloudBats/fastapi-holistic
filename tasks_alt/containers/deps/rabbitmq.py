from invoke import task

from ..docker_utils import Volume, Service

AMPQ_PORT = 5672
HTTP_MANAGEMENT_PORT = 15672
DEFAULT_BITNAMI_NODE_NAME = "rabbit@localhost"
# TODO: see how to create queues on startup
#   https://stackoverflow.com/questions/58266688/how-to-create-a-queue-in-rabbitmq-upon-startup
service = Service(
    image_name="bitnami/rabbitmq",
    image_tag="3",
    container_name="rabbitmq",
    environment=dict(
        RABBITMQ_USERNAME="rabbit",
        RABBITMQ_PASSWORD="rabbit",
    ),
    published_ports=[AMPQ_PORT, HTTP_MANAGEMENT_PORT],
)


@task
def test(c):
    c.run(
        "docker exec"
        " --interactive --tty"
        f" {service.container_name}"
        " rabbitmqctl status",
        pty=True
    )


@task
def client(c):
    c.run("echo NOT IMPLEMENTED")


@task
def client_docker(c):
    c.run(
        "docker run"
        " --interactive --tty"
        " --rm"
        f" --network {service.network}"
        f" {service.image}"
        # rabbitmqctl -n {RABBITMQ_DEFAULT_BITNAMI_NODE_NAME} status
        f" rabbitmqctl -n rabbit@{service.container_name} status",
        pty=True
    )
