"""Tests des composants de l'onglet Territoires."""

from components.charts import couverture_map

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
    assert list(geo.marker.color) == [331694.0, 50213.0]  # couleur = dimension
    assert list(geo.marker.size) == [2103778.0, 516092.0]  # taille = population
    assert geo.marker.colorbar.title.text == "Trajets desservis"


def test_couverture_map_empty_does_not_crash() -> None:
    assert len(couverture_map([], "Trajets desservis").data[0].lat) == 0
