from __future__ import annotations

import logging.handlers
import sys

from loguru import logger
from loguru._logger import Logger

from . import exception_ext, gcp


DEFAULT_CUSTOM_THIRD_PARTY_LEVEL = logging.WARNING
CUSTOM_LEVELS_BY_ROOT_NAME = {
    "requests": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "urllib3": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "asyncio": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "concurrent": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "google": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "grpc": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    # pyasn1 initial level is logging.DEBUG instead of the usual logging.WARNING
    "pyasn1": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "rsa": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
    "vcr": DEFAULT_CUSTOM_THIRD_PARTY_LEVEL,
}
LOG_FORMAT_DELIMITER = " | "
# loguru outputs the message as part of the record dict in serialize mode
# TODO: see if this helps in cloud logging, otherwise change to nothing
LOG_FORMAT_STRUCTURED = "{message}"
# this follows loguru._defaults.LOGURU_FORMAT
LOG_FORMAT_TERMINAL_FIELDS = (
    # Use {time} to include local time zone and {time:!UTC} for the same but converted to UTC time
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS!UTC}</green>",
    "<level>{level: <8}</level>",
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>",
    "<level>{message}</level>",
    "{extra}",
)


def init_logging(
    log_level: int = logging.INFO,
    log_format_terminal: str = None,
    log_format_structured: str = None,
    # TODO: create different format for exceptions
    # TODO: use this to format exceptions differently in both structured and terminal formats
    # log_format_exception: str = None,
    log_format_delimiter: str = LOG_FORMAT_DELIMITER,
    use_structured_logging: bool = False,
    use_verbose_exceptions: bool = False,
    use_stdlib_logging_propagation: bool = False,
    use_gcp_logging: bool = False,
) -> None:
    if use_gcp_logging:
        use_structured_logging = True

    if not log_format_terminal:
        log_format_terminal = log_format_delimiter.join(LOG_FORMAT_TERMINAL_FIELDS)

    if not log_format_structured:
        log_format_structured = LOG_FORMAT_STRUCTURED

    log_format = log_format_structured if use_structured_logging else log_format_terminal

    # disable verbose logging in production to avoid exposing sensitive data
    if log_level != logging.DEBUG or use_structured_logging:
        use_verbose_exceptions = False

    init_logging_root(
        log_level,
        use_stdlib_logging_propagation,
    )
    init_loguru(
        log_level,
        log_format,
        use_structured_logging,
        use_verbose_exceptions,
        use_stdlib_logging_propagation,
        use_gcp_logging,
    )


def init_logging_root(log_level: int, use_stdlib_logging_propagation: bool) -> None:
    # taken from loguru docs, DO NOT MODIFY, customizations should be done in handlers
    # https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
    class StdLibLoggingInterceptHandler(logging.Handler):
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

    logging.root.setLevel(log_level)

    # some libraries add their own loggers at import and need their level adjusted
    #  to prevent verbose debug and info logging
    for name in get_python_logging_library_loggers():
        for prefix, level in CUSTOM_LEVELS_BY_ROOT_NAME.items():
            if name.startswith(prefix):
                logging.getLogger(name).setLevel(level)

    if not use_stdlib_logging_propagation:
        intercept_handler = StdLibLoggingInterceptHandler()
        logging.root.handlers = [intercept_handler]
        for name in get_logger_root_names():
            logging.getLogger(name).handlers = [intercept_handler]
            logging.getLogger(name).propagate = False

    # TODO: see if this method has any advantages over the current one, otherwise remove
    # alternative method which removes all handlers and lets everything propagate to root logger
    # for name in logging.root.manager.loggerDict:
    #     logging.getLogger(name).handlers = []
    #     logging.getLogger(name).propagate = True


def init_loguru(
    log_level: int,
    log_format: str,
    use_structured_logging: bool,
    use_verbose_exceptions: bool,
    use_stdlib_logging_propagation: bool,
    use_google_cloud_logging: bool,
) -> None:
    class StdLibLoggingPropagationHandler(logging.Handler):
        CUSTOM_FORMAT_DELIMITER = " |~| "
        CUSTOM_FORMAT = CUSTOM_FORMAT_DELIMITER.join(("{message}", "{extra}", ""))

        def emit(self, record):
            import ast
            import pprint

            message, extra, traceback = record.msg.split(
                StdLibLoggingPropagationHandler.CUSTOM_FORMAT_DELIMITER, maxsplit=2
            )
            record.msg = message
            if not use_structured_logging:
                try:
                    extra_as_obj = ast.literal_eval(extra)
                except SyntaxError:
                    record.msg += f"\n{extra}"
                else:
                    if extra_as_obj:
                        record.msg += f"\n{pprint.pformat(extra_as_obj, width=120)}"
            if traceback:
                record.msg += f"\n{traceback}"
            logging.getLogger(record.name).handle(record)

    # enqueue=True ensures async logging and avoids concurrent access of the sink in multiprocessing
    # diagnose shows values but is very verbose, should only be there for debug
    diagnose = use_verbose_exceptions
    shared = dict(
        enqueue=True,
        level=log_level,
        serialize=use_structured_logging,
        format=log_format,
        backtrace=True,
        diagnose=diagnose,
    )
    logger.configure(handlers=[])

    if use_stdlib_logging_propagation:
        # the format is not modifiable when directing logs to the stdlib logging propagator
        shared.update(format=StdLibLoggingPropagationHandler.CUSTOM_FORMAT)
        logger.add(StdLibLoggingPropagationHandler(), **shared)

        return

    if use_google_cloud_logging:
        logger.add(sink=gcp.get_cloud_logging_handler(), **shared)
        # TODO: see why it's not getting triggered, probably logger variable scope not module
        # logger.patch(add_google_cloud_items)

        return

    # TODO: see if the simplified version is enough, stdlib only uses stderr by default and this isn't a CLI
    # logger.add(sink=sys.stdout, filter=lambda record: not record["exception"], **shared)
    # logger.add(sink=sys.stderr, filter=lambda record: record["exception"], **shared)
    logger.add(sink=sys.stderr, **shared)


# disabled due to not being triggered by logger.patch()
# def add_google_cloud_items(record: Record) -> None:
#     print("in add_google_cloud_items")
#     record["extra"]["jsonPayload"] = {"test": "string"}


# inspired from blog article
# https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
def get_logger_root_names() -> set[str]:
    result = set()
    for name in [
        *get_python_logging_library_loggers(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in result:
            result.add(name.split(".")[0])

    return result


def get_python_logging_library_loggers() -> dict[str, logging.Logger]:
    return logging.root.manager.loggerDict


# this can be used for customizing individual routes
# # ensures all exceptions are marked correctly so we can filter them later by the flag
# exception_logger = logger.bind(is_exception=True)
#
# # reraise is required, otherwise the app will never return 500
# @route.get(...)
# @exception_logger.catch(reraise=True)
# def ...


def escape_curly_brackets(value: str) -> str:
    """Prevents loguru string format errors"""
    # TODO: test
    return value.replace("{", "}}").replace("}", "{{")


def log_exception_structured(logger_: Logger, exc: Exception) -> None:
    logger_.exception(escape_curly_brackets(str(exc)), **exception_ext.get_exception_items(exc))


# WARNING: monkey patching
# this allows calling logger.exception_structured(exc) instead of log_exception_structured(logger, exc)
Logger.exception_structured = log_exception_structured.__get__(None, Logger)
