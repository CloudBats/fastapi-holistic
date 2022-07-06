from pathlib import Path

from invoke import task
import dotenv

from . import run

DOT_ENV_FILE_NAME = ".env"
LOCAL_DEFAULTS_ENV_FILE_NAME = ".env-local-defaults"
cwd = Path.cwd()


def load_dotenv_in_env() -> None:
    dotenv.load_dotenv()


def get_env_local_defaults() -> dict:
    return dotenv.dotenv_values(LOCAL_DEFAULTS_ENV_FILE_NAME)


@task
def curlme(c):
    c.run('curl -w "\n%{http_code}\n" localhost:' + run.PORT)
