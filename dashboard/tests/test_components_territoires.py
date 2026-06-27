"""Tests des composants de l'onglet Territoires."""

from components.charts import couverture_bars, couverture_map

_POINTS = [
    {
        "citycode": "75056",
        "city_name": "Paris",
        "geo": {"lat": 48.85, "lon": 2.35},
        "population": 2103778.0,
        "valeur": 331694.0,
        "has_gare": True,
    },
    {
        "citycode": "69123",
        "city_name": "Lyon",
        "geo": {"lat": 45.76, "lon": 4.84},
        "population": 516092.0,
        "valeur": 50213.0,
        "has_gare": True,
    },
]


def test_couverture_map_encodes_dimension_and_population() -> None:
    fig = couverture_map(_POINTS, "Trajets desservis")
    geo = fig.data[0]
    assert list(geo.lat) == [48.85, 45.76]
    # Couleur = dimension ramenée en milliers.
    assert list(geo.marker.color) == [331.694, 50.213]
    assert list(geo.marker.size) == [2103778.0, 516092.0]  # taille = population
    assert geo.marker.colorbar.title.text == "Trajets desservis"


def test_couverture_map_handles_null_valeur() -> None:
    points = [{**_POINTS[0], "valeur": None}]
    assert list(couverture_map(points, "Distance à la gare").data[0].marker.color) == [0.0]


def test_couverture_map_empty_does_not_crash() -> None:
    assert len(couverture_map([], "Trajets desservis").data[0].lat) == 0


_COUVERTURE = {
    "by": "code_dept",
    "mailles": [
        {
            "cle": "75",
            "nb_communes": 1,
            "taux_avec_gare": 1.0,
            "nb_trajets_total": 331694,
            "accessibilite_moy": 3.0,
        },
        {
            "cle": "69",
            "nb_communes": 1,
            "taux_avec_gare": 1.0,
            "nb_trajets_total": 50213,
            "accessibilite_moy": 3.0,
        },
    ],
}


def test_couverture_bars_sorted_largest_on_top() -> None:
    fig = couverture_bars(_COUVERTURE)
    bar = fig.data[0]
    assert bar.orientation == "h"
    assert list(bar.x) == [50213, 331694]  # inversé : plus desservi en haut
    assert bar.y[-1] == "75"
    assert list(bar.marker.color) == [1.0, 1.0]  # couleur = taux de gare


def test_couverture_bars_empty_does_not_crash() -> None:
    fig = couverture_bars({"by": "code_region", "mailles": []})
    assert len(fig.data[0].x) == 0
