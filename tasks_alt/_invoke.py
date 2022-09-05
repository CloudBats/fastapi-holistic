from subprocess import run

from . import config


# TODO: add pipx check
def install_with_pipx():
    """Install invoke for general purpose script running, along with dotenv to enable .env file support in invoke.
    Expects pipx to be available in the env."""
    for command in (
        f'pipx install --pip-args "{config.pip_args()}" "invoke~=1.0"',
        f'pipx inject --pip-args "{config.pip_args()}" "invoke" --include-apps "python-dotenv[cli]~=0.20"',
    ):
        run(command, shell=True)


if __name__ == "__main__":
    install_with_pipx()
