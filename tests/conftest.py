from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING

from _pytest.logging import caplog as _caplog
from loguru import logger
import pytest


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest

# TODO: see how to use this after setting up pytest-compatible logging in the app
# required to use caplog to test log output, taken from loguru docs, DO NOT MODIFY
# https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog
@pytest.fixture
def caplog(_caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropagateHandler(), format="{message} {extra}")

    yield _caplog

    logger.remove(handler_id)


def normalize_file_stem(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", value.lower()).rstrip("_")


def build_cassette_path(request: FixtureRequest, custom_file_stem: str = None) -> str:
    test_case_name = normalize_file_stem(request.node.name)
    module = request.node.fspath
    file_name = f"{custom_file_stem or test_case_name}.yaml"
    vcr_cassette_path = Path(module.dirname) / "cassettes" / module.purebasename / file_name

    return str(vcr_cassette_path)
