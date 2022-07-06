from invoke import task

import os


@task
def pre_start(c):
    """Reserved for stateful actions that must happen before the web server starts.

    DO NOT use to install os or python packages."""

    # c.run("app-db-probe")


GUNICORN_CONF = os.getenv("GUNICORN_CONF", "scripts/gunicorn_conf.py")
APP_MODULE = os.getenv("APP_MODULE", "app.app:app")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "8080")

# TODO: check .venv dir exists via ".venv/bin/python -m pip -V"


@task(pre_start)
def start_gunicorn(c):
    """Start Gunicorn with Uvicorn workers, with debug and live reload."""

    env = dict(HOST=HOST, PORT=PORT)
    # TODO: see is --preload is desirable https://docs.gunicorn.org/en/stable/settings.html#preload-app
    c.run(f'exec .venv/bin/gunicorn --config "{GUNICORN_CONF}" "{APP_MODULE}"', env=env)


@task(pre_start)
def start_gunicorn_dev(c):
    """Start Gunicorn with Uvicorn workers, with debug and live reload."""
    env = dict(HOST=HOST, PORT=PORT, LOG_LEVEL="debug", GUNICORN_MAX_WORKERS="2")
    c.run(f'exec .venv/bin/gunicorn --config "{GUNICORN_CONF}" --reload "{APP_MODULE}"', env=env)


@task(pre_start)
def start_uvicorn_dev(c):
    """Start Uvicorn with live reload."""
    env = dict(UVICORN_HOST=HOST, UVICORN_PORT=PORT, UVICORN_LOG_LEVEL="debug")
    c.run(f'exec .venv/bin/uvicorn --reload "{APP_MODULE}"', env=env)
