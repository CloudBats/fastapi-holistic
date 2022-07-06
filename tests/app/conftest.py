# https://fastapi.tiangolo.com/advanced/testing-dependencies/
# https://fastapi.tiangolo.com/advanced/testing-database/
import contextlib
from typing import Any, Generator

import fastapi.testclient
import pytest
import sqlalchemy.orm
import vcr

import app.app
import app.database.session
import app.deps
import app.models.base_model
import app.settings


@pytest.fixture(scope="session", autouse=True)
def app_config() -> Generator[app.settings.Default, None, None]:
    from app import app_config

    yield app_config


def db_session_override() -> Generator[sqlalchemy.orm.Session, None, None]:
    """Kept identical to the original since we are using a real DB instance to test."""
    db_session = None
    try:
        db_session = app.database.session.SessionLocal()
        yield db_session
    finally:
        if db_session is not None:
            db_session.close()


db_session = pytest.fixture(db_session_override)


@pytest.fixture(scope="session")
def app_instance() -> fastapi.FastAPI:
    app_ = app.app.app
    app_.dependency_overrides[app.deps.db_session] = db_session_override

    yield app_


@pytest.fixture(scope="session")
def vcr_config() -> dict[str, Any]:
    """Config used primarily for pytest recording and reused for VCR.py"""
    return dict(
        filter_headers=["authorization"],
        filter_post_data_parameters=["login_id", "api_key"],
        ignore_localhost=True,
    )


@pytest.fixture(scope="session")
def vcrpy(vcr_config, record_mode) -> vcr.VCR:
    """Same usage as original VCR.py package"""
    return vcr.VCR(**vcr_config, record_mode=record_mode or "none")


@pytest.fixture(autouse=True)
def sql_db() -> None:
    engine = app.database.session.engine
    metadata = app.database.session.Base.metadata

    with contextlib.closing(engine.connect()) as connection:
        trans = connection.begin()

        # supposedly this should ensure that children are deleted before parents
        for table in reversed(metadata.sorted_tables):
            connection.execute(table.delete())

        trans.commit()


@pytest.fixture
def client(app_instance) -> fastapi.testclient.TestClient:
    yield fastapi.testclient.TestClient(app_instance)
