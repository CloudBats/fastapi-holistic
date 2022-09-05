from invoke import task

from . import cassandra
from . import mysql
from . import elasticsearch
from . import rabbitmq
from . import postgres

# TODO: investigate what the selenium images are for


@task(
    # TODO: see why more than one non-decorator task won't run as prerequisites
    # cassandra.service.up_task,
    # mysql.service.up_task,
    # elasticsearch.service.up_task,
    # rabbitmq.service.up_task,
    # postgres.service.up_task,
    post=[cassandra.create_keyspaces]
)
def all_up(c):
    cassandra.service.up(c),
    mysql.service.up(c),
    elasticsearch.service.up(c),
    rabbitmq.service.up(c),
    postgres.service.up(c),


@task(
    # TODO: see why more than one non-decorator task won't run as prerequisites
    # cassandra.service.down_task,
    # mysql.service.down_task,
    # elasticsearch.service.down_task,
    # rabbitmq.service.down_task,
    # postgres.service.down_task,
)
def all_down(c):
    cassandra.service.down(c),
    mysql.service.down(c),
    elasticsearch.service.down(c),
    rabbitmq.service.down(c),
    postgres.service.down(c),
