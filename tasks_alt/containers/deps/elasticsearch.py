from invoke import task

from ..docker_utils import Volume, Service

service = Service(
    image_name="elasticsearch",
    # TODO: fix the following error
    # ERROR ==> Invalid kernel settings. Elasticsearch requires at least: vm.max_map_count = 262144
    # requires setting: node.store.allow_mmap: false
    # https://github.com/bitnami/bitnami-docker-elasticsearch/issues/61
    # image_name="bitnami/elasticsearch",
    image_tag="8",
    container_name="elasticsearch",
    hostname="elasticsearch",
    volumes=[
        Volume(
            source_relative="db/elasticsearch/config/devbox/elasticsearch.yml",
            # for the elasticsearch image
            destination_absolute="/usr/share/elasticsearch/config/elasticsearch.yml",
            # for the bitnami/elasticsearch image
            # destination_absolute="/opt/bitnami/elasticsearch/config/elasticsearch.yml",
        ),
    ],
    environment=dict(
        HEAP_NEWSIZE="800M",
    ),
    published_ports=[9200, 9300],
)
DEFAULT_USER = "admin"
DEFAULT_PASSWORD = "elasticadmin"


@task
def test(c):
    c.run("curl localhost:9200")
