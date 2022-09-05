from subprocess import run

from . import config


# TODO: see about using PIPX_BIN_DIR=/usr/bin for root user
def install_with_system():
    """Install pipx to enable isolated installation of python tools."""
    run(f'{config.pip_install_command(interpreter="system")} --upgrade --user "pipx~={config.PIPX_MIN_VERSION}"', shell=True)


if __name__ == "__main__":
    install_with_system()
