"""Tests de la politique de logs et des exceptions métier."""

import json
import logging

from exceptions import ModelUnavailableError, ObRailError
from logging_config import JsonFormatter


def _record(**kwargs: object) -> logging.LogRecord:
    record = logging.LogRecord("obrail.test", logging.INFO, __file__, 1, "hello", None, None)
    for key, value in kwargs.items():
        setattr(record, key, value)
    return record


def test_json_formatter_emits_valid_json_with_context() -> None:
    record = _record(method="GET", path="/health", status=200, duration_ms=1.2)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "obrail.test"
    assert payload["msg"] == "hello"
    assert payload["method"] == "GET" and payload["status"] == 200


def test_json_formatter_includes_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            "obrail.test", logging.ERROR, __file__, 1, "failed", None, sys.exc_info()
        )
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exc"]


def test_obrail_error_defaults_and_override() -> None:
    assert ObRailError("x").status_code == 500
    custom = ObRailError("nope", status_code=404, code="not_found")
    assert custom.status_code == 404 and custom.code == "not_found"
    assert ModelUnavailableError("no model").status_code == 503
    assert ModelUnavailableError("no model").code == "model_unavailable"
