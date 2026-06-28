"""Test d'intégration du simulateur (POST /fragilite/predict) - modèle live réel.

Ignoré si les artefacts .joblib sont absents (ex. CI sans data/).
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app

_MODEL_FILE = Path(settings.model_dir) / "cluster_fragilite.joblib"
_skip = pytest.mark.skipif(not _MODEL_FILE.exists(), reason="modèle .joblib absent")

# Commune urbaine dense avec gare (profil « pôle urbain »).
_URBAIN = {
    "has_gare": True,
    "population": 2_000_000,
    "densite_pop_km2": 20_000,
    "part_65plus": 0.18,
    "revenu_median_uc": 30_000,
    "nb_lignes_total": 12,
    "nb_trajets_moy_arret": 800,
    "amplitude_moy_h": 18.0,
    "taux_sans_voiture": 0.6,
    "distance_dom_trav_med_km": 5.0,
    "dist_gare_min_m": 300,
}


@_skip
def test_predict_urban_with_gare() -> None:
    with TestClient(app) as client:
        data = client.post("/api/v1/fragilite/predict", json=_URBAIN).json()
    assert data["cluster"] in (0, 1)  # strate « avec gare »
    assert data["niveau_fragilite"] is not None
    assert data["cluster_nom"] is not None


@_skip
def test_predict_rural_without_gare() -> None:
    rural = {
        **_URBAIN,
        "has_gare": False,
        "population": 300,
        "densite_pop_km2": 15,
        "dist_gare_min_m": 12_000,
    }
    with TestClient(app) as client:
        data = client.post("/api/v1/fragilite/predict", json=rural).json()
    assert data["cluster"] not in (0, 1)  # strate « sans gare »


@_skip
def test_predict_imputes_missing_fields() -> None:
    with TestClient(app) as client:
        # Seul has_gare fourni : les autres champs sont imputés par médiane.
        resp = client.post("/api/v1/fragilite/predict", json={"has_gare": True})
    assert resp.status_code == 200
