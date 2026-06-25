"""Tests d'intégration des endpoints stats (API + base seed via TestClient)."""

from fastapi.testclient import TestClient


def test_overview_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/stats/overview")
    assert response.status_code == 200

    data = response.json()
    assert data["total_trajets"] == 15
    assert data["nb_operateurs"] == 4  # SNCF, ÖBB, DB, Trenitalia
    assert data["part_nuit"] == 0.2  # 3 trains de nuit / 15
    assert data["nb_pays"] == 3  # FR, DE, IT
    assert data["nb_villes_desservies"] > 0
    assert 0 < data["part_transfrontalier"] < 1


def test_jour_nuit_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/stats/jour-nuit").json()
    assert data["nuit"]["nb_trajets"] == 3
    assert data["jour"]["nb_trajets"] == 12
    assert data["nuit"]["part"] == 0.2


def test_operateurs_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/stats/operateurs?limit=5").json()
    assert len(data) == 4  # SNCF, ÖBB, DB, Trenitalia
    assert data[0]["agency_name"] == "SNCF"
    assert data[0]["nb_trajets"] == 11  # opérateur le plus présent dans le seed


def test_operateurs_endpoint_respects_limit(client: TestClient) -> None:
    data = client.get("/api/v1/stats/operateurs?limit=2").json()
    assert len(data) == 2
