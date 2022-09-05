from dataclasses import dataclass
from typing import Optional, List, Dict

from invoke import task
from invoke.context import Context
from invoke.tasks import Task
from .. import config


def format_env_options(variables: Optional[dict] = None, file_name: Optional[str] = None) -> str:
    env_options = "".join(f" --env {k}={v}" for k, v in variables.items()) if variables else ""
    env_file_option = f" --env-file {file_name}" if file_name and (config.CWD / file_name).is_file() else ""

    return env_options + env_file_option


def format_arg_options(variables: dict) -> str:
    return "".join(f" --build-arg {k}={v}" for k, v in variables.items()) if variables else ""


def format_build_command(
    tag: str, path: Optional[str] = None, target: Optional[str] = None, args: Optional[dict] = None
) -> str:
    return (
        f"docker build"
        f" --tag {tag}"
        f" --target={target if target else tag}"
        f"{format_arg_options(args)}"
        f" {path if path else '.'}"
    )


@dataclass
class Volume:
    source_relative: str
    destination_absolute: str
    type: str = "bind"
    readonly: bool = True

    def format_mount_option(self):
        return (
            f" --mount"
            f" type={self.type}"
            f",src={config.CWD}/{self.source_relative}"
            f",dst={self.destination_absolute}"
            f",readonly" if self.readonly else ""
        )


class Service:
    def __init__(
        self,
        image_name: str,
        image_tag: str = "latest",
        container_name: Optional[str] = None,
        hostname: Optional[str] = None,
        network: str = config.APP_NETWORK,
        volumes: Optional[List[Volume]] = None,
        user: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        exposed_ports: Optional[List[int]] = None,
        published_ports: Optional[List[int]] = None,
        command: Optional[str] = None,
    ) -> None:
        self._image_name: str = image_name
        self._image_tag: str = image_tag
        self.container_name: str = container_name if container_name is not None else self._image_name
        self.hostname: str = hostname if hostname is not None else self.container_name
        self.network: str = network
        self.volumes: List[Volume] = volumes if volumes is not None else list()
        # TODO: raise error if command is an empty string
        self.user: str = user
        self.environment: Dict[str, str] = environment if environment is not None else dict()
        self.exposed_ports: List[int] = exposed_ports if exposed_ports is not None else list()
        self.published_ports: List[int] = published_ports if published_ports is not None else list()
        # TODO: raise error if command is an empty string
        self.command: str = command

    @property
    def image(self) -> str:
        return f"{self._image_name}:{self._image_tag}"

    @property
    def mount_options(self) -> str:
        return "".join(v.format_mount_option() for v in self.volumes)

    @property
    def published_ports_option(self) -> str:
        return "".join(f" --publish {config.LOCAL_HOST}:{p}:{p}" for p in self.published_ports)

    @property
    def user_option(self) -> str:
        return f" --user {self.user}" if self.user is not None else ""

    @property
    def command_argument(self) -> str:
        return f" {self.command}" if self.command is not None else ""

    @property
    def environment_options(self) -> str:
        return "".join(f" --env {k}={v}" for k, v in self.environment.items())

    @property
    def run_script_shared_parts(self) -> str:
        return (
            f" --name {self.container_name}"
            f" --hostname {self.hostname}"
            f" --network {self.network}"
            # TODO: add exposed ports and compare with published
            f"{self.published_ports_option}"
            f"{self.mount_options}"
            f"{self.user_option}"
            f"{self.environment_options}"
            f" {self.image}"
            f"{self.command_argument}"
        )

    @property
    def up_script(self) -> str:
        return (
            "docker run"
            " --detach"
            f"{self.run_script_shared_parts}"
            f"{self.command_argument}"
        )

    def up(self, c):
        c.run(self.up_script)

    @property
    def up_task(self):
        return task(self.up)

    @property
    def up_with_interactive_console_script(self) -> str:
        return (
            "docker run"
            " --interactive --tty"
            " --rm"
            f"{self.run_script_shared_parts}"
            f" /bin/bash"
        )

    @property
    def exec_interactive_console_script(self) -> str:
        return (
            "docker exec"
            " --interactive --tty"
            f" {self.container_name}"
            f" /bin/bash"
        )

    def console(self, c):
        c.run(self.exec_interactive_console_script)

    @property
    def console_task(self):
        return task(self.console)

    def format_run_with_custom_command_script(self, command: str) -> str:
        return (
            "docker run"
            " --rm"
            f"{self.run_script_shared_parts}"
            # TODO: raise error if command is empty string
            f" {command}"
        )

    @property
    def down_scripts(self):
        return (
            f"docker container stop {self.container_name}",
            f"docker container rm {self.container_name}",
        )

    def down(self, c):
        for command in self.down_scripts:
            c.run(command, warn=True)

    @property
    def down_task(self):
        return task(self.down)

    def logs(self, c):
        c.run(f"docker logs {self.container_name}")

    @property
    def logs_task(self):
        return task(self.logs)

    def logs_follow(self, c):
        c.run(f"docker logs {self.container_name} --follow")

    @property
    def logs_follow_task(self):
        return task(self.logs_follow)

    @property
    def all_tasks(self) -> List[Task]:
        return [
            self.up_task,
            self.down_task,
            self.console_task,
            self.logs_task,
            self.logs_follow_task,
        ]
