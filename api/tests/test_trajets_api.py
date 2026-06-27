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


def test_list_trajets_default(client: TestClient) -> None:
    data = client.get("/api/v1/trajets").json()
    assert data["total"] == 15  # 15 trajets dans le seed
    assert data["page"] == 1
    assert len(data["items"]) == 15  # page_size 50 par défaut
    assert "trip_id" in data["items"][0]


def test_list_trajets_filter_night(client: TestClient) -> None:
    data = client.get("/api/v1/trajets?is_night=true").json()
    assert data["total"] == 3  # 3 trains de nuit
    assert all(item["is_night_train"] for item in data["items"])


def test_list_trajets_pagination(client: TestClient) -> None:
    data = client.get("/api/v1/trajets?page_size=5").json()
    assert len(data["items"]) == 5
    assert data["pages"] == 3  # ceil(15 / 5)


def test_list_trajets_sort_distance_desc(client: TestClient) -> None:
    items = client.get("/api/v1/trajets?sort=-distance_km&page_size=3").json()["items"]
    distances = [item["distance_km"] for item in items]
    assert distances == sorted(distances, reverse=True)


def test_distance_histogram_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/trajets/distances?bin_km=100").json()
    assert data["bin_km"] == 100
    total = sum(b["count_jour"] + b["count_nuit"] for b in data["bins"])
    nuit = sum(b["count_nuit"] for b in data["bins"])
    assert total == 15  # 15 trajets train dans le seed
    assert nuit == 3  # 3 trains de nuit
    mins = [b["min_km"] for b in data["bins"]]
    assert mins == sorted(mins)  # bins ordonnés
