import os
from pathlib import Path

CWD = Path.cwd()

# TODO: add a virtual env checks for tasks that use the active python interpreter
CURRENT_VENV = os.getenv("VIRTUAL_ENV")
VENV_DIR = os.getenv("VENV_DIR", "venv")

# TODO: allow python and python3 as alternatives, check version >= 3.9
SYSTEM_PYTHON_PATH = "/usr/bin/python3"
NON_SYSTEM_PYTHON_PATH = "/usr/local/bin/python3"
# The official Python docker image has the fully working python3 install at "/usr/local/bin/python3"
PYTHON_PATH = NON_SYSTEM_PYTHON_PATH if Path(NON_SYSTEM_PYTHON_PATH).is_file() else SYSTEM_PYTHON_PATH

# TODO: verify this actually works, and version
INTERPRETER_COMMAND_BY_TYPE = dict(
    system=f"{PYTHON_PATH}",
    local=f"{VENV_DIR}/bin/python",
    active="python",
)


def pip_args(cache_dir=""):
    cache_dir_option = f" --cache-dir {cache_dir}" if cache_dir else " --no-cache-dir"

    return f" --disable-pip-version-check{cache_dir_option}"


def pip_install_command(interpreter="active", cache_dir=""):
    interpreter_command = INTERPRETER_COMMAND_BY_TYPE[interpreter]

    return f"{interpreter_command} -m pip {pip_args(cache_dir)} install --progress-bar off"


REQUIREMENTS_FILE = "requirements.txt"

POETRY_VERSION = "1.2.0"
PIPX_MIN_VERSION = "1.0"

APP_IMAGE_NAME = "app-dev"
APP_CONTAINER_NAME = "app-dev"
APP_USER = "apps"
APP_USER_ID = 6000
APP_GROUP_ID = 6000

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = os.getenv("APP_PORT", "8000")

LOCAL_HOST = "0.0.0.0"
APP_NETWORK = "app"

# TODO: move to app component config
CONTAINER_NAME_SUFFIX = ""
