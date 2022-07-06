# =====================
# GENERAL CONFIGURATION
# =====================

# DO NOT MODIFY WITHOUT A VERY GOOD REASON. INSPIRATION:
# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
# https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/docker-images/gunicorn_conf.py

import os


def get_web_concurrency():
    web_concurrency_str = os.getenv("WEB_CONCURRENCY")
    if web_concurrency_str:
        web_concurrency = int(web_concurrency_str)
        if web_concurrency <= 0:
            raise ValueError("Web concurrency (worker count) must be positive.")

        return web_concurrency

    import multiprocessing

    # https://docs.gunicorn.org/en/stable/design.html#how-many-workers
    # We recommend (2 x $num_cores) + 1 as the number of workers to start off with.
    #  While not overly scientific, the formula is based on the assumption that for a given core,
    #  one worker will be reading or writing from the socket while the other worker is processing a request.
    default_web_concurrency = float(os.getenv("GUNICORN_WORKERS_PER_CORE", "2")) * multiprocessing.cpu_count() + 1
    web_concurrency = max(int(default_web_concurrency), 2)
    max_workers_str = os.getenv("GUNICORN_MAX_WORKERS")

    return min(web_concurrency, int(max_workers_str)) if max_workers_str else web_concurrency


# Gunicorn config variables
loglevel = os.getenv("LOG_LEVEL", "info")
# '-' means log to stdout
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-") or None
# '-' means log to stderr
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-") or None
workers = get_web_concurrency()
bind = os.getenv("WEB_BIND") or f'{os.getenv("HOST", "0.0.0.0")}:{os.getenv("PORT", "8080")}'
worker_tmp_dir = "/dev/shm"
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEP_ALIVE", "5"))

DEBUG_DATA = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    "graceful_timeout": graceful_timeout,
    "timeout": timeout,
    "keepalive": keepalive,
    "errorlog": errorlog,
    "accesslog": accesslog,
}

# =====================
# LOGGING CONFIGURATION
# =====================

try:
    from loguru import logger
except ImportError:
    import json

    # TODO: see if the loguru branch logs this
    print(json.dumps(DEBUG_DATA))
else:
    import logging

    import gunicorn.glogging

    # class taken from loguru docs, DO NOT MODIFY, customizations should be done in handlers
    # https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    class InterceptedGunicornLogger(gunicorn.glogging.Logger):
        def setup(self, cfg):
            handler = InterceptHandler()
            level = logging.getLevelName(os.environ.get("LOG_LEVEL", "debug").upper())

            self.error_logger = logging.getLogger("gunicorn.error")
            self.error_logger.handlers = [handler]
            self.error_logger.setLevel(level)

            self.access_logger = logging.getLogger("gunicorn.access")
            self.access_logger.handlers = [handler]
            self.access_logger.setLevel(level)

    is_deployed_locally = os.environ.get("ENVIRONMENT") in (None, "", "local", "test")
    if not is_deployed_locally:
        import sys

        logger.configure(handlers=[])
        logger.add(sink=sys.stderr, level=loglevel.upper(), diagnose=False, serialize=True, format="{message}")

    logger_class = InterceptedGunicornLogger

    # disabled for now, reloading oddly works only for the first change
    # to enable, also modify the startup line in start.sh and remove the conf file option:
    # exec gunicorn -c "$GUNICORN_CONF" "$APP_MODULE"

    # from uvicorn.workers import UvicornWorker
    #
    #
    # class DebugUvicornWorker(UvicornWorker):
    #     CONFIG_KWARGS = UvicornWorker.CONFIG_KWARGS | dict(reload=True)
    #
    #
    # worker_class = "scripts.gunicorn_conf.DebugUvicornWorker"
    # reload = True
