# Import all the models, so that Base has them before being
# imported by Alembic
# TODO: check if this is used
from app.models.base_model import Base  # noqa: F401

# from app.models.my_model import MyModel  # noqa: F401
