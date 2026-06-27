"""Tests des composants de l'onglet Fragilité (fonctions pures, sans API)."""

from components.charts import cluster_effectifs_bars, cluster_profils_parallel, clusters_map

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
