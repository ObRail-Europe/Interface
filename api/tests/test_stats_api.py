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
