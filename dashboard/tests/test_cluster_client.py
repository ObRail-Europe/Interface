"""Test du client fragilité : construction des requêtes."""

from typing import Any

import pytest

from api.cluster_client import HttpClusterClient


def test_get_carte_builds_query(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(self: HttpClusterClient, path: str) -> list[Any]:
        captured["path"] = path
        return []

    monkeypatch.setattr(HttpClusterClient, "_get", fake_get)
    client = HttpClusterClient("http://api")

    client.get_carte()
    assert captured["path"] == "/api/v1/clusters/carte"

    client.get_carte(code_region="11")
    assert captured["path"] == "/api/v1/clusters/carte?code_region=11"


def test_summaries_and_profils_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []
    monkeypatch.setattr(HttpClusterClient, "_get", lambda self, path: captured.append(path) or [])
    client = HttpClusterClient("http://api")
    client.get_summaries()
    client.get_profils()
    assert captured == ["/api/v1/clusters", "/api/v1/clusters/profils"]


def test_predict_posts_features(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(self: HttpClusterClient, path: str, json: Any) -> dict[str, Any]:
        captured["path"] = path
        captured["json"] = json
        return {"cluster": 0, "cluster_nom": "c0", "niveau_fragilite": "Faible"}

    monkeypatch.setattr(HttpClusterClient, "_post", fake_post)
    client = HttpClusterClient("http://api")
    result = client.predict({"has_gare": True, "population": 20000})

    assert captured["path"] == "/api/v1/fragilite/predict"
    assert captured["json"] == {"has_gare": True, "population": 20000}
    assert result["cluster"] == 0
