from contextlib import AbstractContextManager
import os


from . import config


# TODO: see if this is better as an attribute instead of a function
def get_wheel_path():
    for path in (config.CWD / "dist").iterdir():
        if path.name.endswith(".whl"):
            return path

    return None


# copied from python 3.11
# https://github.com/python/cpython/pull/28271/files
class chdir(AbstractContextManager):
    """Non thread-safe context manager to change the current working directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())


def wait_for_connection(host: str, port: int, timeout_seconds: int = 300) -> None:
    import socket
    import time

    service = (host, port)
    start = time.monotonic()
    while True:
        if time.monotonic() - start > timeout_seconds:
            print(f"Service {service} is not reachable in {timeout_seconds} seconds, continuing anyway...")

            break

        try:
            socket.create_connection(service, timeout=0.5).close()
        except socket.error:
            continue

        print(f"Service {service} reachable.")

        break
