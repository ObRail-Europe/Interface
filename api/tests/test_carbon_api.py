"""Tests d'intégration des endpoints carbone (API + base seed train + vols)."""

from fastapi.testclient import TestClient

_PATH = "/api/v1/stats/co2/comparaison-avion"


def test_comparaison_avion_endpoint(carbon_client: TestClient) -> None:
    data = carbon_client.get(_PATH).json()
    assert data["facteur_avion_g_par_pkm"] == 230.0  # défaut documenté
    assert data["par_tranche"]  # au moins une tranche de distance
    # Prendre le train évite du CO₂ : estimation avion > émissions réelles train.
    assert data["co2_avion_estime_t"] > data["co2_train_total_t"]
    assert data["co2_evite_t"] > 0
    # Cohérence : évité = avion estimé − train réel.
    ecart = data["co2_avion_estime_t"] - data["co2_train_total_t"]
    assert abs(data["co2_evite_t"] - ecart) < 1e-6


def test_comparaison_avion_factor_is_parameterizable(carbon_client: TestClient) -> None:
    base = carbon_client.get(_PATH).json()
    doubled = carbon_client.get(f"{_PATH}?facteur_avion_g_par_pkm=460").json()
    assert doubled["facteur_avion_g_par_pkm"] == 460.0
    # Doubler le facteur double l'estimation avion (le train réel ne bouge pas).
    assert doubled["co2_avion_estime_t"] == base["co2_avion_estime_t"] * 2
    assert doubled["co2_train_total_t"] == base["co2_train_total_t"]
