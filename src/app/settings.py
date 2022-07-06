# pylint: disable=too-few-public-methods

from __future__ import annotations

import os
from typing import Any, Optional

import dotenv
from pydantic import BaseSettings, PostgresDsn

from fastapi_laser.pydantic_ext import update_empty_attrs_from_other, update_empty_attrs_from_secrets, validator


ENVIRONMENT_KEY = "ENVIRONMENT"
env_local_defaults = dotenv.dotenv_values(".env-local-defaults")


class BaseInnerLocalConfig:
    # Uncomment the lines below to load vars from local .env file using dotenv
    env_file = ".env"
    env_file_encoding = "utf-8"

    # Uncomment one of the lines below to read secret files from the location
    #  the files are read based on the attr name in the enclosing class
    # secrets_dir = "/run"  # new style ephemeral dir using mounted tmpfs
    # secrets_dir = "/var/run"  # old style ephemeral dir
    # secrets_dir = "/run/secrets"  # docker standard secrets location


class Postgres(BaseSettings):
    scheme: str = "postgresql"
    host: Optional[str]
    port: Optional[int]
    user: Optional[str]
    password: Optional[str]
    db: Optional[str]
    uri: Optional[PostgresDsn]

    _OVERRIDE_FIELD_KEYS = ("host", "port", "user", "password", "db")

    class Config(BaseInnerLocalConfig):
        env_prefix = "postgres_"

    @classmethod
    def empty_instance(cls) -> Postgres:
        return cls(host=None, port=None, user=None, password=None, db=None, uri=None)

    @classmethod
    def instance_with_local_defaults(cls) -> Postgres:
        local_default_items = {
            k: v for k in cls._OVERRIDE_FIELD_KEYS if (v := env_local_defaults.get(f"postgres_{k}".upper()))
        }

        return cls(**local_default_items)

    def with_update_from_other(self, other: Postgres) -> Postgres:
        update_empty_attrs_from_other(self, other, *Postgres._OVERRIDE_FIELD_KEYS)

        return self

    def with_update_from_secrets(self, secrets: dict[str, str]) -> Postgres:
        update_empty_attrs_from_secrets(self, secrets, *Postgres._OVERRIDE_FIELD_KEYS)

        if not self.uri:
            self.uri = PostgresDsn.build(
                scheme=self.scheme or "",
                user=self.user or "",
                password=self.password or "",
                host=self.host or "",
                port=str(self.port or ""),
                path=f"/{self.db or ''}",
            )

        return self


class Default(BaseSettings):
    """
    Loads configuration from the environment seamlessly
    and acts as an interface for all app settings.

    Attribute names are automatically upper cased for the env lookup.

    Field value priority

    In the case where a value is specified for the same Settings field in multiple ways,
    the selected value is determined as follows (in descending order of priority):

    1. Arguments passed to the Settings class initialiser.
    2. Environment variables, e.g. my_prefix_special_function as described above.
    3. Variables loaded from a dotenv (.env) file.
    4. Variables loaded from the secrets directory.
    5. The default field values for the Settings model.

    Field order is important in models for the following reasons:
    - validation is performed in the order fields are defined; fields validators
      can access the values of earlier fields, but not later ones
    - field order is preserved in the model schema
    - field order is preserved in validation errors
    - field order is preserved by .dict() and .json() etc.

    All fields with annotations (whether annotation-only or with a default value)
    will precede all fields without an annotation.
    Within their respective groups, fields remain in the order they were defined.

    See the docs:
    https://pydantic-docs.helpmanual.io/usage/settings
    https://pydantic-docs.helpmanual.io/usage/validators/
    https://pydantic-docs.helpmanual.io/usage/models/#field-ordering

    To patch an object you can use the following pattern:
      in Default:
          obj = dict(a=1, b=2)
      in Subclass either of these two work, the first one is the safest:
          obj = Default.__fields__["obj"].default | dict(b=5)
          obj = Default().obj | dict(b=5)

    Validators are used to transform values and/or validate complex cases.
    Wrapped function signature must be (cls, value, values, config, field),
    with values, config and field optional.
    The values argument exposes all previously validated attributes.
    """

    environment: str = "local"
    # WARNING: do not modify the default, it can lead to exposing sensitive data in production.
    log_level: str = "info"
    """Logging level. Anything above debug is considered safe in production."""
    _log_level = validator("log_level")(lambda v: v.upper())
    use_structured_logging: bool = True
    use_stdlib_logging_propagation: bool = False
    """When enabled, Loguru propagates all logs to stdlib logging.

    Intended for use with external tools that use stdlib logging, e.g. pytest.
    """

    secrets_key: str = ""
    # TODO: see how to use this, currently validators aren't seeing it in the values dict
    # secrets: Json[dict[str, str]]
    secrets: dict[str, str] = dict()

    @validator("secrets")
    def _secrets(cls, v: dict[str, str], values: dict[str, Any]) -> dict[str, str]:
        # TODO: implement validation
        return v

    postgres: Postgres = Postgres.empty_instance()

    @validator("postgres")
    def _postgres(cls, v: Postgres, values: dict[str, Any]) -> Postgres:
        return Postgres().with_update_from_other(v).with_update_from_secrets(values["secrets"])

    _OVERRIDES = dict()

    class Config:
        # Uncomment the line below to load vars from the environment with the specified prefix
        # env_prefix = "currencycloud_bank_service"

        pass


class Local(Default):
    """Local development with external communication"""

    environment = "local"
    log_level = "debug"
    use_structured_logging = False
    postgres = Postgres.instance_with_local_defaults()

    class Config(BaseInnerLocalConfig):
        pass


class Test(Default):
    """Local test runs with no external communication, also used for CI pipelines.

    Reserved for pytest."""

    environment = "test"
    log_level = "debug"
    use_structured_logging = False
    use_stdlib_logging_propagation: bool = True
    postgres = Postgres.instance_with_local_defaults()

    _OVERRIDES = dict(secrets_key="")


class Dev(Default):
    """Application run in development mode in the cloud"""

    environment = "dev"
    log_level = "debug"


class Staging(Default):
    """Application run in staging mode in the cloud"""

    environment = "staging"


class Prod(Default):
    """Application run in production mode in the cloud"""

    environment = "prod"


def get_environment():
    return os.environ.get(ENVIRONMENT_KEY) or Default.__fields__["environment"].default


def get_settings() -> Default:
    class_or_default = globals().get(get_environment().capitalize(), Default)

    return class_or_default(**class_or_default._OVERRIDES)
