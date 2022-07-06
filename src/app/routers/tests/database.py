from fastapi_laser import fastapi_ext

from app.database.session import engine, reset_schema
from app.models import base_model


router = fastapi_ext.get_router()


@router.get("/tables")
def test_read_currencies():
    return engine.table_names()


@router.get("/metadata")
def test_read_metadata():
    return repr(base_model.Base.metadata.sorted_tables)


@router.post("/nuke")
def test_nuke_database():
    reset_schema()
    base_model.Base.metadata.create_all(bind=engine)
