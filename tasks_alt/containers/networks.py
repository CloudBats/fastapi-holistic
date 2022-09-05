from invoke import task


from .. import config


@task
def app_up(c):
    c.run(f"docker network create {config.APP_NETWORK}")


@task
def app_down(c):
    c.run(f"docker network rm {config.APP_NETWORK}")
