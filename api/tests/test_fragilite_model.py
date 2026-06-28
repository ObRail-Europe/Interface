"""Tests unitaires du modèle de fragilité (artefacts synthétiques, sans fichier)."""

import math

from ml.fragilite_model import FragiliteModel

# Modèle : 1 feature (population) par strate, centroïdes en espace log1p.
_MODEL = {
    "cluster_nom": {0: "petite", 1: "grande", 2: "sans gare"},
    "fragilite": {0: "Faible", 1: "Élevée", 2: "Modérée"},
    "clusters_with_gare": [0, 1],
    "clusters_without_gare": [2],
    "centroids": {
        0: [math.log1p(1_000)],
        1: [math.log1p(1_000_000)],
        2: [math.log1p(500)],
    },
}
_PRE = {
    "raw_inputs": [
        "population",
        "dist_gare_min_m",
        "taux_sans_voiture",
        "distance_dom_trav_med_km",
    ],
    "features": ["population"],
    "winsor_bounds": {"population": (0.0, 1e12)},
    "impute_median_values": {},
}


def test_predict_picks_nearest_centroid_in_stratum() -> None:
    model = FragiliteModel(_MODEL, _PRE)
    petite = model.predict({"population": 2_000}, has_gare=True)
    grande = model.predict({"population": 800_000}, has_gare=True)
    assert petite.cluster == 0 and petite.niveau_fragilite == "Faible"
    assert grande.cluster == 1 and grande.cluster_nom == "grande"


def test_predict_respects_has_gare_stratification() -> None:
    model = FragiliteModel(_MODEL, _PRE)
    # Sans gare : seule la strate {2} est candidate, quelle que soit la population.
    result = model.predict({"population": 1_000_000}, has_gare=False)
    assert result.cluster == 2


def test_dist_gare_corrected_is_zeroed_for_gare_communes() -> None:
    model = FragiliteModel(
        {**_MODEL, "centroids": {0: [0.0], 1: [10.0], 2: [math.log1p(5_000)]}},
        {
            **_PRE,
            "features": ["dist_gare_corrected"],
            "winsor_bounds": {"dist_gare_corrected": (0.0, 1e9)},
        },
    )
    # has_gare=True -> dist_gare_corrected=0 -> vecteur [0] -> cluster 0.
    avec = model.predict({"dist_gare_min_m": 5_000}, has_gare=True)
    assert avec.cluster == 0
    # has_gare=False -> dist_gare_corrected=5000 -> log1p(5000) ~ centroïde 2.
    sans = model.predict({"dist_gare_min_m": 5_000}, has_gare=False)
    assert sans.cluster == 2
