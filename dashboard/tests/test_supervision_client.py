"""Test du client supervision : construction de la requête."""

from typing import Any

import pytest

from api.supervision_client import HttpSupervisionClient


def test_health_details_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        HttpSupervisionClient, "_get", lambda self, path: captured.update(path=path) or {}
    )
    HttpSupervisionClient("http://api").get_health_details()
    assert captured["path"] == "/api/v1/health/details"
