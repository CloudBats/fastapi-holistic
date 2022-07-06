from fastapi import Depends, FastAPI

from fastapi_laser import fastapi_ext, logging_ext

from . import app_config, routers


def get_application() -> FastAPI:
    """Returns application object after performing init for everything
    required before the application starts.

    The main purpose of the function is to avoid init on import."""

    # WARNING: DO NOT PLACE ANYTHING ABOVE THIS LINE, logging must come first, the other inits use it internally
    config = dict(
        log_level=app_config.log_level,
        use_structured_logging=app_config.use_structured_logging,
        use_stdlib_logging_propagation=app_config.use_stdlib_logging_propagation,
    )
    if hasattr(app_config, "use_gcp_logging"):
        config.update(
            use_gcp_logging=app_config.use_gcp_logging,
        )
    logging_ext.init_logging(**config)

    # WARNING: DO NOT log anything in this function, it will pollute unit tests

    # include decorators that should apply to all routes here
    dependencies = []

    return FastAPI(dependencies=[Depends(i) for i in dependencies], **fastapi_ext.APP_EXTRA_FIELD_DEFAULTS)


app = get_application()
app.include_router(routers.router)
