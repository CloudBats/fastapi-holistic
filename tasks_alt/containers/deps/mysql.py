from invoke import task

from ..docker_utils import Volume, Service


ROOT_USER = "root"
ROOT_PASSWORD = "root"

mariadb_service = Service(
    image_name="bitnami/mariadb",
    image_tag="10",
    container_name="mysql",
    volumes=[
        Volume(
            source_relative="db/mysql/config/mariadb/my.cnf",
            destination_absolute="/opt/bitnami/mariadb/conf/my_custom.cnf",
        ),
        Volume(
            source_relative="db/mysql/load_devbox_snapshot.sql",
            destination_absolute="/docker-entrypoint-initdb.d/dump.sql",
        ),
    ],
    environment=dict(
        MARIADB_ROOT_USER=ROOT_USER,
        MARIADB_ROOT_PASSWORD=ROOT_PASSWORD,
    ),
    published_ports=[3306],
)


# we can't create other root users in percona
PERCONA_ROOT_USER = "root"
PERCONA_ROOT_PASSWORD = ROOT_PASSWORD
PERCONA_DEFAULT_DATABASE = "mysql"

service = Service(
    image_name="percona",
    image_tag="5.7",
    #image_name="bitnami/percona",
    #image_tag="5.7",
    container_name="mysql",
    volumes=[
        Volume(
            source_relative="db/mysql/create_databases.sql",
            destination_absolute="/docker-entrypoint-initdb.d/create_databases.sql",
        ),
        # WARNING: put all options in the file mounted in the volume below instead of in the command line
        # https://dev.mysql.com/doc/refman/5.6/en/server-option-variable-reference.html
        Volume(
            source_relative="db/mysql/config/my.cnf",
            destination_absolute="/etc/my.cnf.d/my.cnf",
            # for bitnami/percona
            #destination_absolute="/opt/bitnami/mysql/conf/my_custom.cnf",
        ),
    ],
    # TODO: see if we need MYSQL_DATABASE env var
    environment=dict(
        MYSQL_DATABASE=PERCONA_DEFAULT_DATABASE,
        MYSQL_ROOT_PASSWORD=PERCONA_ROOT_PASSWORD,
    ),
    published_ports=[3306],
)


@task
def client(c):
    c.run(
        "docker exec"
        " --interactive --tty"
        f" {service.container_name}"
        f" mysql --host=localhost --user={ROOT_USER} --password={ROOT_PASSWORD}",
        pty=True
    )


# TODO: fix error
@task
def client_docker(c):
    c.run(
        "docker run"
        " --interactive --tty"
        " --rm"
        f" --network {service.network}"
        f" {service.image}"
        f" mysql --host={service.container_name} --user={ROOT_USER} --password={ROOT_PASSWORD}",
        pty=True
    )


# TODO: see if this is worth keeping, mounting the sql file in the right place auto-loads it
@task
def create_databases(c):
    c.run(
        f"docker exec"
        f" {service.container_name}"
        f" /bin/sh -c"
        f"  'mysql --host=localhost --user={ROOT_USER} --password={ROOT_PASSWORD}'"
        "   < /db/mysql/create_databases.sql/create_databases.sql",
        pty=True,
    )
