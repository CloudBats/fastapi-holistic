from typing import Callable

from fastapi_laser import fastapi_ext

from . import settings


version = "0.1.0"

app_config = settings.get_settings()
module_based_router_factory: Callable = fastapi_ext.get_module_based_router_factory(environment=app_config.environment)
