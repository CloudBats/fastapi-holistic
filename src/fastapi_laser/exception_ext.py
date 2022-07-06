from __future__ import annotations

from dataclasses import dataclass, field, InitVar
import re
from typing import Any, TYPE_CHECKING, Union

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import type_ext


if TYPE_CHECKING:
    from loguru._logger import Logger


@dataclass
class BasePackageError(Exception):
    """Base class for all errors in this package.

    Automatically creates a message item in the detail dictionary with the child docstring.
    """

    detail: dict[str, Any] = field(default_factory=dict)
    """The dictionary where all information ends up in.

    Intended to be consumed by router middleware, mainly for logging.
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    response: Union[dict[str, Any], BaseModel] = field(default_factory=dict)
    """Supply a response dictionary to propagate it when raising in the endpoint.

    Intended to be consumed by router middleware for returning a response. Ignored if empty.
    """
    inner_exception: InitVar[Exception] = None
    """When re-raising an exception, supply it here to merge its members to the detail dict.
    """
    message: InitVar[str] = None
    """Optional message. supplemental to exception docstring.

    Merged into detail dict.
    """

    def __post_init__(self, inner_exception, message):
        self.detail.update(help=self.__doc__)
        self.detail.update(message=message or format_exception_type(self))
        if inner_exception:
            self.detail.update(inner_exception=get_exception_items(inner_exception))

    @classmethod
    def from_detail_object(cls, obj: Any) -> BasePackageError:
        return cls(dict(detail=jsonable_encoder(obj)))

    def with_response(self, response: Union[dict[str, Any], BaseModel]) -> BasePackageError:
        self.response = response

        return self

    def log_structured(self, logger: Logger) -> None:
        # TODO: see why logger.exception() produces the following error:
        # --- Logging error in Loguru Handler #1 ---
        # Record was: None
        # TypeError: __init__() missing 4 required positional arguments: 'verb', 'route', 'params', and 'response'
        logger.error(self.logging_message, **self.detail)

    @property
    def logging_message(self) -> str:
        return self.detail["message"]

    @property
    def endpoint_response(self) -> JSONResponse:
        return JSONResponse(
            content=self.response_as_dict or self.detail,
            status_code=self.status_code,
            headers=getattr(self, "headers", None),
        )

    @property
    def response_as_dict(self) -> dict[str, Any]:
        return self.response.dict() if isinstance(self.response, BaseModel) else self.response

    @property
    def route_response_def(self) -> dict[int, dict]:
        if not isinstance(self.response, BaseModel):
            raise TypeError(f"Expected response schema, received {type(self.response)}")

        return {self.status_code: {"model": type(self.response), "description": self.__doc__}}


def format_exception_type(exc: Exception) -> str:
    return re.sub(r"([A-Z])", r" \1", type(exc).__name__).lstrip().lower().capitalize() + " occurred."


def get_exception_items(exc: Exception) -> dict:
    # TODO: include class bases
    result = dict()
    try:
        result.update(exception_name=type(exc).__name__)
        result.update(exception_bases=jsonable_encoder(i.__name__ for i in type(exc).__bases__))
        if isinstance(exc, BasePackageError):
            exception_dict = exc.detail
        else:
            exception_dict = jsonable_encoder(dict(type_ext.get_public_data_attribute_pairs(exc)))
        result.update(exception_dict=exception_dict)
        result.update(exception_repr=repr(exc))
    finally:
        return result
