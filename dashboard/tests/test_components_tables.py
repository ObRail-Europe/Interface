"""Tests des composants de la table des trajets (fonctions pures, sans API)."""

from components.tables import sort_param, trajets_table


def test_trajets_table_is_server_side() -> None:
    table = trajets_table()
    assert table.id == "trajets-table"
    assert table.page_action == "custom"  # pagination côté serveur
    assert table.sort_action == "custom"  # tri côté serveur
    col_ids = {col["id"] for col in table.columns}
    assert {"departure_city", "arrival_city", "distance_km"} <= col_ids


def test_sort_param_default() -> None:
    assert sort_param(None) == "id"
    assert sort_param([]) == "id"


def test_sort_param_direction() -> None:
    assert sort_param([{"column_id": "distance_km", "direction": "desc"}]) == "-distance_km"
    assert sort_param([{"column_id": "departure_city", "direction": "asc"}]) == "departure_city"
