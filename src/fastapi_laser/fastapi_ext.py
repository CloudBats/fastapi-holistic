import time
from types import ModuleType
from typing import Callable, Optional, Sequence
import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from loguru import logger
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import exception_ext, logging_ext, utils


APP_EXTRA_FIELD_DEFAULTS = dict(worker_requests_count=0)


def get_module_based_router_factory(environment: str) -> Callable:
    """Intended for use in app __init__.py with the environment from app config."""

    def create_router_from_modules(*modules: ModuleType, dependencies: Optional[Sequence[Depends]] = None) -> APIRouter:
        """Creates a router and loads routes based on modules, using their __name__.
        Expects modules to have a router attribute.

        The modules names are transformed into routes as follows:
        - underscores are converted to slashes: foo_bar -> foo/bar
        - characters are lower cased: FooBar -> foobar
        """
        router = get_router(dependencies=dependencies)
        for module in modules:
            # exclude tests from prod environment
            route_name = format_route_name(module.__name__)
            if environment != "prod" or route_name != "tests":
                router.include_router(module.router, prefix=f"/{route_name}")

        return router

    return create_router_from_modules


def format_route_name(module_name: str) -> str:
    return module_name.split(".")[-1].replace("_", "/").lower()


def get_router(*, dependencies: Optional[Sequence[Depends]] = None) -> APIRouter:
    """Use this instead of APIRouter to ensure logging works as intended."""
    return APIRouter(route_class=EnhancedLoggingRoute, dependencies=dependencies)


def remove_authorization_header(request_headers: Headers) -> dict[str, str]:
    request_headers_as_dict = dict(request_headers)
    request_headers_as_dict.pop("authorization", None)

    return request_headers_as_dict


# alternative middleware pattern from the official docs
# https://fastapi.tiangolo.com/advanced/custom-request-and-route/
class EnhancedLoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request.app.extra["worker_requests_count"] += 1
            request_cloud_logging_items = dict(
                request_method=request.method,
                request_url=str(request.url),
                remote_ip=f"{request.client.host}:{request.client.port}",
            )
            # TODO: see how to include requirements from the auth middleware to use request.user
            # TODO: add user agent
            # user-agent: "curl/7.68.0"

            # label keys are not automatically converted to camelCase, they need to be supplied as such
            labels = dict(httpRequestUrlPath=request.url.path)
            if client_id := request.headers.get("x-settle-client-id"):
                labels.update(clientId=client_id)

            # TODO: experiment with logger.opt(exception=False).contextualize
            with logger.contextualize(
                # TODO: get trace id from open telemetry or open census
                trace=uuid.uuid4().hex,
                worker_requests_count=request.app.extra["worker_requests_count"],
                http_request=request_cloud_logging_items,
                labels=labels,
            ):
                # TODO see that consuming body or json from the request doesn't create generator-related problems
                #   https://github.com/tiangolo/fastapi/issues/394
                request_headers_as_dict = remove_authorization_header(request.headers)
                request_extra = dict(
                    body=(await request.body()).decode(),
                    headers=request_headers_as_dict,
                    query_params=dict(request.query_params),
                    path_params=request.path_params,
                )
                logger.info("Request received.", **request_extra)
                start_time = time.perf_counter()
                start_cpu_time = utils.get_cpu_time()

                try:
                    # hand execution over to framework to process request
                    response: Response = await original_route_handler(request)
                except StarletteHTTPException as exc:
                    logging_ext.log_exception_structured(logger, exc)
                    response = await http_exception_handler(request, exc)
                except RequestValidationError as exc:
                    logging_ext.log_exception_structured(logger, exc)
                    response = await request_validation_exception_handler(request, exc)
                except exception_ext.BasePackageError as exc:
                    exc.log_structured(logger)
                    response = exc.endpoint_response
                except Exception as exc:  # pylint: disable=broad-except
                    logging_ext.log_exception_structured(logger, exc)
                    response = JSONResponse(
                        dict(detail="Internal Server Error"),
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        headers=getattr(exc, "headers", None),
                    )

                elapsed_time = time.perf_counter() - start_time
                elapsed_cpu_time = utils.get_cpu_time() - start_cpu_time
                request_cloud_logging_items |= dict(status=response.status_code, latency=f"{elapsed_time:.3f}s")
                response_extra = dict(
                    total_time_ms=int(elapsed_time * 1000),
                    cpu_time_ms=int(elapsed_cpu_time * 1000),
                    headers=dict(response.headers),
                    body=response.body.decode(),
                    http_request=request_cloud_logging_items,
                )
                logger.info("Response sent.", **response_extra)

                response.headers["X-Response-Time"] = str(elapsed_time)
                # TODO: add tracing header

                return response

        return custom_route_handler
