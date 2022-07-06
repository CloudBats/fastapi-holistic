from fastapi import status
from loguru import logger

from app import module_based_router_factory

from . import database, error


router = module_based_router_factory(database, error)


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    logger.debug("I'm the debug log message!")
    logger.info("I'm the info log message!")
    logger.warning("I'm the warning log message!")
    logger.error("I'm the error log message!")
    logger.critical("I'm the critical log message!")

    return dict(msg="Tests API root.")
