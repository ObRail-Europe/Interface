"""Tests des composants graphiques (fonctions pures, sans API)."""

from components.charts import departs_map, jour_nuit_donut, operateurs_bar


def test_jour_nuit_donut_values() -> None:
    fig = jour_nuit_donut(
        {"jour": {"nb_trajets": 12, "part": 0.8}, "nuit": {"nb_trajets": 3, "part": 0.2}}
    )
    pie = fig.data[0]
    assert list(pie.labels) == ["Jour", "Nuit"]
    assert list(pie.values) == [12, 3]
    assert pie.hole == 0.6


def test_operateurs_bar_orders_largest_on_top() -> None:
    fig = operateurs_bar(
        [
            {"agency_name": "SNCF", "nb_trajets": 11, "part_nuit": 0.1},
            {"agency_name": "ÖBB", "nb_trajets": 2, "part_nuit": 1.0},
        ]
    )
    bar = fig.data[0]
    assert len(bar.x) == 2
    assert list(bar.x) == [2, 11]  # inversé : barres horizontales empilées de bas en haut
    assert bar.y[-1] == "SNCF"  # plus gros volume en haut


def test_departs_map_points() -> None:
    fig = departs_map(
        [
            {"citycode": "75056", "city_name": "Paris", "lat": 48.85, "lon": 2.35, "nb_trajets": 6},
            {"citycode": "69123", "city_name": "Lyon", "lat": 45.76, "lon": 4.84, "nb_trajets": 2},
        ]
    )
    geo = fig.data[0]
    assert list(geo.lat) == [48.85, 45.76]
    assert list(geo.lon) == [2.35, 4.84]
    assert list(geo.marker.color) == [6, 2]


def test_departs_map_empty_does_not_crash() -> None:
    assert len(departs_map([]).data[0].lat) == 0
