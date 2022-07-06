from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import status

from fastapi_laser.exception_ext import BasePackageError


@dataclass
class ErrorWithResponse(BasePackageError):
    response: dict = field(default_factory=dict)


@dataclass
class DuplicateKeyIdempotencyError(BasePackageError):
    """More than one record found with requested unique id."""

    kind: str = None
    id: str = None
    status_code: int = status.HTTP_502_BAD_GATEWAY


@dataclass
class ContentsMismatchIdempotencyError(BasePackageError):
    """Record found with requested unique id but failed to match expected field values."""

    kind: str = None
    id: str = None
    expected: dict = None
    received: dict = None
    status_code: int = status.HTTP_409_CONFLICT
