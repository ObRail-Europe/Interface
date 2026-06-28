"""Tests d'intégration de l'endpoint de santé détaillée (V9.1)."""

from fastapi.testclient import TestClient


def test_health_details_lists_services(client: TestClient) -> None:
    data = client.get("/api/v1/health/details").json()
    by_name = {s["nom"]: s for s in data["services"]}
    assert {"api", "database"} <= set(by_name)
    assert by_name["api"]["statut"] == "up"
    assert by_name["database"]["statut"] == "up"  # base seed disponible
    assert by_name["database"]["latence_ms"] >= 0
