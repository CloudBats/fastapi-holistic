from typing import Sequence, Union

import sqlalchemy.orm

from app import app_config
from app.models.base_model import Base


engine = sqlalchemy.create_engine(app_config.postgres.uri, pool_pre_ping=True)
SessionLocal = sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


def as_committed(obj: Union[Base, Sequence[Base]], session: sqlalchemy.orm.Session) -> Union[Base, Sequence[Base]]:
    add_and_commit(obj, session)
    # TODO: add check for instanceof list
    if isinstance(obj, Base):
        session.refresh(obj)
    else:
        for o in obj:
            # TODO: find a way to perform this as a bulk transaction
            session.refresh(o)

    return obj


def add_and_commit(obj: Union[Base, Sequence[Base]], session: sqlalchemy.orm.Session) -> None:
    # TODO: add check for instanceof list
    adder = session.add if isinstance(obj, Base) else session.add_all
    adder(obj)
    session.commit()


def reset_schema():
    engine.execute(
        "DROP SCHEMA public CASCADE;"
        "CREATE SCHEMA public;"
        "GRANT ALL ON SCHEMA public TO postgres;"
        "GRANT ALL ON SCHEMA public TO public;"
        "COMMENT ON SCHEMA public IS 'standard public schema';"
    )
