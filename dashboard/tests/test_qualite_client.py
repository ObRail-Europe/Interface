"""Test du client qualité : construction des requêtes."""

from typing import Any

import pytest

from api.qualite_client import HttpQualiteClient


def test_qualite_client_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []
    monkeypatch.setattr(HttpQualiteClient, "_get", lambda self, path: captured.append(path) or {})
    client = HttpQualiteClient("http://api")

    client.get_completude("villes")
    client.get_anomalies()
    client.get_volumetrie()

    assert captured == [
        "/api/v1/qualite/completude?table=villes",
        "/api/v1/qualite/anomalies",
        "/api/v1/qualite/volumetrie",
    ]


def test_completude_defaults_to_trajets(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        HttpQualiteClient, "_get", lambda self, path: captured.update(path=path) or {}
    )
    HttpQualiteClient("http://api").get_completude()
    assert captured["path"] == "/api/v1/qualite/completude?table=trajets"
