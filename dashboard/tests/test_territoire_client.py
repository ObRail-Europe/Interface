"""Test du client territoires : construction de la requête carte."""

from typing import Any

import pytest

from api.territoire_client import HttpTerritoireClient


def test_get_carte_builds_query(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(self: HttpTerritoireClient, path: str) -> list[Any]:
        captured["path"] = path
        return []

    monkeypatch.setattr(HttpTerritoireClient, "_get", fake_get)
    client = HttpTerritoireClient("http://api")
    client.get_carte("has_gare", code_dept="75", has_gare=True)

    path = captured["path"]
    assert path.startswith("/api/v1/villes/carte?")
    assert "dimension=has_gare" in path
    assert "code_dept=75" in path
    assert "code_region" not in path  # None écarté
    assert "has_gare=true" in path


def test_get_couverture_builds_query(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(self: HttpTerritoireClient, path: str) -> dict[str, Any]:
        captured["path"] = path
        return {"by": "code_region", "mailles": []}

    monkeypatch.setattr(HttpTerritoireClient, "_get", fake_get)
    HttpTerritoireClient("http://api").get_couverture("code_region")

    assert captured["path"] == "/api/v1/stats/couverture?by=code_region"


def test_get_amplitude_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(self: HttpTerritoireClient, path: str) -> dict[str, Any]:
        captured["path"] = path
        return {"bin_h": 1.0, "part_apres_minuit": 0.0, "bins": []}

    monkeypatch.setattr(HttpTerritoireClient, "_get", fake_get)
    HttpTerritoireClient("http://api").get_amplitude()

    assert captured["path"] == "/api/v1/stats/amplitude"
