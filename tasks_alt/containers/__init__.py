from invoke import task


from . import deps
from . import app


@task(deps.all_up, app.initial_migrations_local, app.service.up_task)
def local_all_up(c):
    pass


@task(app.service.down_task, deps.all_down)
def local_all_down(c):
    pass


@task(local_all_down, deps.all_up, app.initial_migrations_local, app.test, local_all_down)
def local_test_clean(c):
    pass


@task
def system_all_down(c):
    c.run("docker stop $(docker ps -a -q)")
    c.run("docker rm $(docker ps -a -q)")
