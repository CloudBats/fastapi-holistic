import logging

from loguru import logger
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

import app.database.session


MAX_ATTEMPT_COUNT = 60 * 5
WAIT_SECONDS = 1


@retry(
    stop=stop_after_attempt(MAX_ATTEMPT_COUNT),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def db_health_check():
    logger.info("Checking DB...")
    # logger.info(app_config)

    try:
        db = app.database.session.SessionLocal()
        # Try to create session to check if DB is awake
        db.execute("SELECT 1")
    except Exception as e:
        logger.error(e)
        raise e

    logger.info("DB OK.")
