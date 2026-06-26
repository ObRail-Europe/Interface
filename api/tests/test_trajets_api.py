"""Tests d'intégration des endpoints de l'explorateur (API + base seed)."""

from fastapi.testclient import TestClient


def test_liaisons_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/trajets/liaisons?limit=50").json()
    # 11 paires O-D entièrement résolues côté FR dans le seed (étranger/Nice exclus)
    assert len(data) == 11

    paris_lyon = next(
        liaison
        for liaison in data
        if liaison["departure_city"] == "Paris" and liaison["arrival_city"] == "Lyon"
    )
    assert paris_lyon["departure"]["lat"] == 48.8566
    assert paris_lyon["nb_trajets"] == 1


def test_liaisons_endpoint_respects_limit(client: TestClient) -> None:
    assert len(client.get("/api/v1/trajets/liaisons?limit=3").json()) == 3
