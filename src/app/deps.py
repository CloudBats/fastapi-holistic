from typing import Generator

from fastapi import HTTPException
import sqlalchemy.orm

import app.database.session

from . import app_config


def db_session() -> Generator[sqlalchemy.orm.Session, None, None]:
    session_ = None
    try:
        session_ = app.database.session.SessionLocal()
        yield session_
    finally:
        if session_ is not None:
            session_.close()


async def lock_for_migration():
    raise HTTPException(503, detail="Service locked for migration, try again soon.")
