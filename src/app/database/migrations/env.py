"""This is a script file ran via alembic, not used as part of the package.

Thus, imports must be absolute.
"""

# https://alembic.sqlalchemy.org/en/latest/autogenerate.html

# TODO: make logging work with loguru
# from logging.config import fileConfig
from alembic import context
from alembic.config import Config
from loguru import logger
from sqlalchemy import MetaData

from fastapi_laser.alembic_ext.metadata import get_connectable, get_migration_config_items, render_item_factory

from app import app_config
from app.models.base_model import Base


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# DOWNSTREAM AUTHOR NOTE:
# not restricted to alembic.ini, context.config can be set programmatically
config: Config = context.config

# TODO: make logging work with loguru
# Interpret the config file for Python logging.
# This line sets up loggers basically.
# fileConfig(config.config_file_name)


# add your model's MetaData object here for 'autogenerate' support
target_metadata: MetaData = Base.metadata


# other values from the config, defined by the needs of env.py, can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# my_important_option = config.get_section_option("section_name", "my_important_option")


# get_migration_config_items adds template_args, don't include it manually here
context_configure_items = dict(
    target_metadata=target_metadata,
    compare_type=True,
    render_item=render_item_factory(),
)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.
    By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    context.configure(url=app_config.postgres.uri, literal_binds=True, **context_configure_items)
    with context.begin_transaction():
        logger.info("Running offline migrations...")
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    with get_connectable(config).connect() as connection:
        context.configure(
            connection=connection, **(context_configure_items | get_migration_config_items(config, target_metadata))
        )
        with context.begin_transaction():
            logger.info("Running online migrations...")
            # engine = context.get_context().connection
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
