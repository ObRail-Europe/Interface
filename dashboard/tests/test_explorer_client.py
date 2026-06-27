"""Test du client explorateur : construction de la requête de liste."""

from typing import Any

import pytest

from api.explorer_client import HttpExplorerClient


def test_list_trajets_builds_query(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def fake_get(self: HttpExplorerClient, path: str) -> dict[str, Any]:
        captured["path"] = path
        return {"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0}

    monkeypatch.setattr(HttpExplorerClient, "_get", fake_get)
    client = HttpExplorerClient("http://api")
    client.list_trajets(
        {"mode": "train", "departure_city": None, "agency_name": ""},
        sort="-distance_km",
        page=2,
        page_size=50,
    )

    path = captured["path"]
    assert path.startswith("/api/v1/trajets?")
    assert "mode=train" in path
    assert "departure_city" not in path  # None écarté
    assert "agency_name" not in path  # vide écarté
    assert "sort=-distance_km" in path
    assert "page=2" in path
    assert "page_size=50" in path
