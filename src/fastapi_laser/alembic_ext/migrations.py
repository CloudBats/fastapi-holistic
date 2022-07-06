from dataclasses import dataclass
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from loguru import logger
import sqlalchemy.exc
import sqlalchemy.orm


# configuration:
# https://alembic.sqlalchemy.org/en/latest/tutorial.html
# https://alembic.sqlalchemy.org/en/latest/api/config.html

# advanced patterns:
# https://alembic.sqlalchemy.org/en/latest/cookbook.html

# running alembic from python instead of shell:
# https://stackoverflow.com/questions/24622170/using-alembic-api-from-inside-application-code

# commands:
# https://alembic.sqlalchemy.org/en/latest/api/commands.html


def get_config(script_location: str, sqlalchemy_url: str) -> Config:
    config = Config()
    config_main_options = {
        # for .egg packages (?)
        # "script_location": "myapp:migrations"
        "script_location": script_location,
        "sqlalchemy.url": sqlalchemy_url,
        "timezone": "UTC",
        # "version_locations": "%(here)s/versions"
    }
    config_section_options = {}
    for k, v in config_main_options.items():
        config.set_main_option(k, v)
    for section, items in config_section_options.items():
        for k, v in items.items():
            config.set_section_option(section, k, v)

    return config


@dataclass
class Migration:
    config: Config

    @classmethod
    def from_config_args(cls, script_location: str, sqlalchemy_url: str) -> "Migration":
        return cls(get_config(script_location, sqlalchemy_url))

    def generate(self, message: str) -> None:
        logger.info("Generating the migration...")
        command.revision(self.config, message=message, autogenerate=True)

    def upgrade(self, revision: str, sql: bool = False) -> None:
        logger.info(f"Upgrading to {revision} revision...")
        command.upgrade(self.config, revision, sql=sql)

    def upgrade_head(self, sql: bool = False) -> None:
        """Upgrade DB to the latest revision."""
        self.upgrade("head", sql=sql)

    def downgrade(self, revision: str, sql: bool = False) -> None:
        logger.info(f"Downgrading to {revision} revision...")
        command.downgrade(self.config, revision, sql=sql)

    def stamp_head(self) -> None:
        logger.info("Stamping head revision...")
        command.stamp(self.config, "head")

    def head(self) -> str:
        logger.info("Getting head revision...")
        script = ScriptDirectory.from_config(self.config)

        return script.get_current_head()

    @staticmethod
    def current(db_session: sqlalchemy.orm.Session) -> Optional[str]:
        logger.info("Getting current online database revision...")

        try:
            return db_session.execute("SELECT version_num FROM alembic_version").first()[0]
        except sqlalchemy.exc.DatabaseError:
            return None

    def is_current_head(self, db_session: sqlalchemy.orm.Session) -> bool:
        return self.head() == Migration.current(db_session)


# ========================================
# EXPERIMENTAL
# ========================================
# https://alembic.sqlalchemy.org/en/latest/api/runtime.html


def get_script(config):
    return ScriptDirectory.from_config(config)


def my_function(rev, context):
    """do something with
    revision "rev",
    which will be the current database revision,
    and "context",
    which is the MigrationContext that the env.py will create
    """


def run_my_function_in_env(script_location: str, sqlalchemy_url: str):
    config = get_config(script_location, sqlalchemy_url)
    script = get_script(config)
    with EnvironmentContext(
        config, script, fn=my_function, as_sql=False, starting_rev="base", destination_rev="head", tag="sometag"
    ):
        script.run_env()
