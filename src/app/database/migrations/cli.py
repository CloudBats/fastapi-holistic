import pathlib

import typer

from fastapi_laser.alembic_ext.migrations import Migration

from app import app_config


script_location = str(pathlib.Path(__file__).resolve().parent)
# "%" signs from sqlalchemy.url must be escaped
# https://alembic.sqlalchemy.org/en/latest/api/config.html#alembic.config.Config.set_main_option
sqlalchemy_url = app_config.postgres.uri.replace("%", "%%")
migration = Migration.from_config_args(script_location, sqlalchemy_url)

cli = typer.Typer(no_args_is_help=True, help="Alembic migrations")


@cli.command()
def upgrade_head(sql: bool = typer.Option(False)) -> None:
    """Upgrade DB to the latest revision."""
    migration.upgrade("head", sql=sql)


@cli.command()
def upgrade_offline_range(begin: str, end: str) -> None:
    migration.upgrade(f"{begin}:{end}", sql=True)


@cli.command()
def downgrade(revision: str, sql: bool = typer.Option(False)) -> None:
    migration.downgrade(revision, sql=sql)


@cli.command()
def generate(message: str) -> None:
    migration.generate(message)
