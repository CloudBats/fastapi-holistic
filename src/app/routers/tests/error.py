from typing import NoReturn

from fastapi import HTTPException, status

from fastapi_laser import fastapi_ext

from app.exceptions import TestRaiseCustomError


router = fastapi_ext.get_router()


@router.get("/crash")
async def test_crash() -> NoReturn:
    return 1 / 0


@router.get("/raise/http")
async def test_raise_http() -> NoReturn:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/raise/custom")
async def test_raise_custom() -> NoReturn:
    raise TestRaiseCustomError(i_knew_it_was_wrong=True, i_did_it_anyway=True)
