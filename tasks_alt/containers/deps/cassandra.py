from invoke import task

from ..docker_utils import Volume, Service

DEFAULT_USER = "cassandra"
DEFAULT_PASSWORD = "cassandra"
TRANSPORT_PORT = 7000
CQL_PORT = 9042
service = Service(
    image_name="cassandra",
    # image_name="bitnami/cassandra",
    image_tag="4",
    container_name="cassandra",
    environment=dict(
        # used for changing password in the bitnami/cassandra image
        #CASSANDRA_USER=CASSANDRA_DEFAULT_USER,
        #CASSANDRA_SEEDS="cassandra",
        #CASSANDRA_PASSWORD_SEEDER="yes",
        #CASSANDRA_PASSWORD=CASSANDRA_DEFAULT_PASSWORD,
        # in case java options need to be added
        #JVM_EXTRA_OPTS="'-Dcassandra.key=value'",
    ),
    volumes=[
        Volume(
            source_relative="db/cassandra/create_keyspaces.cql",
            destination_absolute="/docker-entrypoint-initdb.d/create_keyspaces.cql",
        ),
        Volume(
            source_relative="db/cassandra/config/local/cassandra.yaml",
            # for the cassandra image
            destination_absolute="/etc/cassandra/cassandra.yaml",
            # for the bitnami/cassandra image
            #destination_absolute="/bitnami/cassandra/conf/cassandra.yaml",
            # TODO: fix the crash to make this readonly = True
            readonly=False,
        ),
    ],
    published_ports=[CQL_PORT],
)


@task
def client(c):
    c.run(
        f"docker exec"
        " --interactive --tty"
        f" {service.container_name}"
        f" cqlsh"
        f"   --username {DEFAULT_USER}"
        f"   --password {DEFAULT_PASSWORD}"
        f"   localhost",
        pty=True,
    )


@task
def client_docker(c):
    c.run(
        "docker run"
        " --interactive --tty"
        " --rm"
        f" --network {service.network}"
        f" {service.image}"
        f" cqlsh"
        f"   --username {DEFAULT_USER}"
        f"   --password {DEFAULT_PASSWORD}"
        f"   {service.container_name}",
        pty=True,
    )


def check_readiness(c) -> bool:
    result = c.run(
        f"docker exec"
        # " --interactive"
        f" {service.container_name}"
        f" cqlsh"
        f"   --username {DEFAULT_USER}"
        f"   --password {DEFAULT_PASSWORD}"
        f"   localhost"
        "    </dev/null;",
        warn=True,
        hide=True,
    )

    return result.exited == 0


@task
def wait_for_readiness(c):
    print("Waiting for Cassandra to be ready...")
    import time

    timeout_seconds = 60
    start = time.monotonic()
    result = False
    while True:
        if time.monotonic() - start > timeout_seconds:
            print(f"Cassandra not ready after {timeout_seconds} seconds, aborting.")

            break

        if not check_readiness(c):
            time.sleep(1)
            continue

        result = True
        print(f"Cassandra ready.")

        break

    return result


@task(wait_for_readiness)
def create_keyspaces(c):
    c.run(
        f"docker exec"
        " --interactive --tty"
        f" {service.container_name}"
        f" cqlsh"
        f"   --username {DEFAULT_USER}"
        f"   --password {DEFAULT_PASSWORD}"
        f"   -f /docker-entrypoint-initdb.d/create_keyspaces.cql localhost",
        pty=True,
    )
