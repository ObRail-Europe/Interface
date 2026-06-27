"""Tests des composants graphiques (fonctions pures, sans API)."""

from components.charts import (
    departs_map,
    distance_histogram,
    jour_nuit_donut,
    liaisons_map,
    operateurs_bar,
)


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


_LIAISONS = [
    {
        "departure_city": "Paris",
        "departure": {"lat": 48.85, "lon": 2.35},
        "arrival_city": "Lyon",
        "arrival": {"lat": 45.76, "lon": 4.84},
        "nb_trajets": 3,
        "part_nuit": 0.0,
        "distance_moy_km": 425.0,
        "co2_moy_par_pkm": 2.4,
    },
    {
        "departure_city": "Lyon",
        "departure": {"lat": 45.76, "lon": 4.84},
        "arrival_city": "Marseille",
        "arrival": {"lat": 43.3, "lon": 5.37},
        "nb_trajets": 1,
        "part_nuit": 1.0,
        "distance_moy_km": 278.0,
        "co2_moy_par_pkm": 2.3,
    },
]


def test_liaisons_map_groups_jour_nuit() -> None:
    # _LIAISONS : Paris→Lyon (part_nuit 0 → jour), Lyon→Marseille (part_nuit 1 → nuit)
    fig = liaisons_map(_LIAISONS)
    assert len(fig.data) == 3  # lignes jour, lignes nuit, points de survol
    assert list(fig.data[0].lat) == [48.85, 45.76, None]  # arc jour Paris→Lyon
    assert list(fig.data[1].lat) == [45.76, 43.3, None]  # arc nuit Lyon→Marseille


def test_liaisons_map_hover_shows_od_and_count() -> None:
    hover = liaisons_map(_LIAISONS).data[2]  # points de survol au milieu des arcs
    assert len(hover.text) == 2
    assert "Paris → Lyon : 3 trajets" in hover.text


def test_liaisons_map_empty_does_not_crash() -> None:
    fig = liaisons_map([])
    assert len(fig.data) == 3
    assert list(fig.data[0].lat) == []


_HISTOGRAM = {
    "bin_km": 100,
    "bins": [
        {"min_km": 0, "max_km": 100, "count_jour": 5, "count_nuit": 1},
        {"min_km": 100, "max_km": 200, "count_jour": 3, "count_nuit": 2},
    ],
}


def test_distance_histogram_is_stacked_jour_nuit() -> None:
    fig = distance_histogram(_HISTOGRAM)
    assert len(fig.data) == 2  # jour + nuit
    assert fig.layout.barmode == "stack"
    assert list(fig.data[0].y) == [5, 3]  # jour
    assert list(fig.data[1].y) == [1, 2]  # nuit


def test_distance_histogram_empty_does_not_crash() -> None:
    fig = distance_histogram({"bin_km": 100, "bins": []})
    assert len(fig.data) == 2
