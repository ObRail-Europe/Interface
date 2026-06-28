"""Tests des composants de l'onglet Fragilité (fonctions pures, sans API)."""

from components.charts import (
    cluster_effectifs_bars,
    cluster_profils_parallel,
    clusters_map,
    fragilite_stacked_bars,
)
from components.fragilite import FIELD_TO_FEATURE, prediction_result, simulator_form

_POINTS = [
    {
        "city_name": "Paris",
        "geo": {"lat": 48.85, "lon": 2.35},
        "cluster": 0,
        "cluster_nom": "c0 - urbain dense",
        "niveau_fragilite": "Faible",
    },
    {
        "city_name": "Lyon",
        "geo": {"lat": 45.76, "lon": 4.84},
        "cluster": 0,
        "cluster_nom": "c0 - urbain dense",
        "niveau_fragilite": "Faible",
    },
    {
        "city_name": "Gap",
        "geo": {"lat": 44.56, "lon": 6.08},
        "cluster": 2,
        "cluster_nom": "c2 - rural",
        "niveau_fragilite": "Élevée",
    },
]


def test_clusters_map_one_trace_per_cluster() -> None:
    fig = clusters_map(_POINTS)
    assert len(fig.data) == 2  # cluster 0 et cluster 2
    names = {trace.name for trace in fig.data}
    assert names == {"c0 - urbain dense", "c2 - rural"}


def test_clusters_map_empty_does_not_crash() -> None:
    assert len(clusters_map([]).data) == 0


_SUMMARIES = [
    {"cluster": 0, "cluster_nom": "c0 - urbain dense", "niveau_fragilite": "Faible", "effectif": 6},
    {"cluster": 2, "cluster_nom": "c2 - rural", "niveau_fragilite": "Élevée", "effectif": 1},
]


def test_cluster_effectifs_bars_largest_on_top() -> None:
    fig = cluster_effectifs_bars(_SUMMARIES)
    bar = fig.data[0]
    assert bar.orientation == "h"
    assert list(bar.x) == [1, 6]  # inversé : plus gros effectif en haut
    assert bar.y[-1] == "c0 - urbain dense"


_PROFILS = [
    {
        "cluster": 0,
        "features": [
            {"nom": "revenu_median_uc", "moyenne": 22000.0, "moyenne_normalisee": 0.8},
            {"nom": "densite_pop_km2", "moyenne": None, "moyenne_normalisee": None},
        ],
    },
    {
        "cluster": 2,
        "features": [
            {"nom": "revenu_median_uc", "moyenne": 26000.0, "moyenne_normalisee": 1.0},
            {"nom": "densite_pop_km2", "moyenne": None, "moyenne_normalisee": None},
        ],
    },
]


def test_cluster_profils_parallel_keeps_only_filled_features() -> None:
    fig = cluster_profils_parallel(_PROFILS)
    dims = fig.data[0].dimensions
    labels = [d.label for d in dims]
    assert labels == ["Revenu"]  # libellé court ; densite_pop_km2 (toute None) écartée
    assert list(dims[0].values) == [0.8, 1.0]


def test_cluster_profils_parallel_empty_does_not_crash() -> None:
    assert len(cluster_profils_parallel([]).data) == 0


def test_field_to_feature_maps_to_api_names() -> None:
    # Les ids du formulaire retombent sur les noms de features attendus par l'API.
    assert FIELD_TO_FEATURE["sim-population"] == "population"
    assert FIELD_TO_FEATURE["sim-dist_gare_min_m"] == "dist_gare_min_m"


def test_simulator_form_has_predict_button_and_gare_selector() -> None:
    text = str(simulator_form())
    assert "sim-predict" in text
    assert "sim-has_gare" in text


_REPARTITION = {
    "by": "code_region",
    "mailles": [
        {
            "cle": "11",
            "repartition": [{"niveau": "Faible", "nb": 3}, {"niveau": "Élevée", "nb": 1}],
        },
        {"cle": "84", "repartition": [{"niveau": "Faible-modérée", "nb": 2}]},
    ],
}


def test_fragilite_stacked_bars_one_trace_per_present_level() -> None:
    fig = fragilite_stacked_bars(_REPARTITION)
    assert fig.layout.barmode == "stack"
    names = [t.name for t in fig.data]
    # Ordre de gravité croissante ; niveaux absents écartés.
    assert names == ["Faible", "Faible-modérée", "Élevée"]
    faible = next(t for t in fig.data if t.name == "Faible")
    assert list(faible.x) == ["11", "84"]
    assert list(faible.y) == [3, 0]  # région 84 n'a pas de « Faible »


def test_prediction_result_shows_cluster_and_level() -> None:
    panel = prediction_result(
        {"cluster": 2, "cluster_nom": "c2 - rural", "niveau_fragilite": "Élevée"}
    )
    text = str(panel)
    assert "Cluster 2" in text
    assert "c2 - rural" in text
    assert "Élevée" in text
