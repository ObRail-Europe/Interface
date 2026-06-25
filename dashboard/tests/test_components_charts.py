"""Tests des composants graphiques (fonctions pures, sans API)."""

from components.charts import jour_nuit_donut, operateurs_bar


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
