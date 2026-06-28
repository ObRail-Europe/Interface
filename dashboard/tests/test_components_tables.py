"""Tests des composants de la table des trajets (fonctions pures, sans API)."""

from components.tables import sort_param, trajet_detail, trajets_table


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


_DETAIL = {
    "id": 7,
    "trip_id": "T7",
    "mode": "train",
    "agency_name": "SNCF",
    "route_long_name": "Paris - Lyon",
    "route_short_name": None,
    "departure_station": None,
    "departure_city": "Paris",
    "departure_time": "07:00:00",
    "arrival_station": None,
    "arrival_city": "Lyon",
    "arrival_time": "09:00:00",
    "distance_km": 425.0,
    "is_night_train": False,
    "co2_per_pkm": 2.4,
    "emissions_co2": 1000.0,
    "service_start_date": "2025-01-01",
    "service_end_date": "2025-12-13",
    "days_of_week": "1111100",
}


def test_trajet_detail_renders_key_fields() -> None:
    panel = trajet_detail(_DETAIL)
    assert panel.children[0].children == "Trajet T7"  # titre
    text = str(panel)
    assert "SNCF" in text
    assert "Paris" in text and "Lyon" in text
