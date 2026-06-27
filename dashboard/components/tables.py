"""Composants de la table des trajets (V2.2) : filtres + table paginée côté serveur."""

from typing import Any

from dash import dash_table, dcc, html

_COLUMNS = [
    {"name": "Trip ID", "id": "trip_id"},
    {"name": "Mode", "id": "mode"},
    {"name": "Opérateur", "id": "agency_name"},
    {"name": "Départ", "id": "departure_city"},
    {"name": "Arrivée", "id": "arrival_city"},
    {"name": "Départ (h)", "id": "departure_time"},
    {"name": "Distance (km)", "id": "distance_km"},
    {"name": "Nuit", "id": "is_night_train"},
    {"name": "CO₂/pkm", "id": "co2_per_pkm"},
]


def filter_controls() -> html.Div:
    """Barre de filtres de la table (alimentent la requête côté serveur)."""
    return html.Div(
        className="filters",
        children=[
            dcc.Dropdown(
                id="f-mode",
                options=[
                    {"label": "Train", "value": "train"},
                    {"label": "Avion", "value": "flight"},
                ],
                placeholder="Mode",
            ),
            dcc.Dropdown(
                id="f-night",
                options=[{"label": "Jour", "value": "jour"}, {"label": "Nuit", "value": "nuit"}],
                placeholder="Jour / Nuit",
            ),
            dcc.Input(id="f-dep-city", type="text", placeholder="Ville de départ", debounce=True),
            dcc.Input(id="f-arr-city", type="text", placeholder="Ville d'arrivée", debounce=True),
            dcc.Input(id="f-agency", type="text", placeholder="Opérateur", debounce=True),
        ],
    )


def trajets_table() -> dash_table.DataTable:
    """Table paginée et triée côté serveur (les données arrivent par callback)."""
    return dash_table.DataTable(
        id="trajets-table",
        columns=_COLUMNS,
        page_action="custom",
        page_current=0,
        page_size=20,
        page_count=0,
        sort_action="custom",
        sort_by=[],
        style_table={"overflowX": "auto"},
        style_cell={"fontSize": "0.85rem", "padding": "4px 8px", "textAlign": "left"},
        style_header={"fontWeight": "bold"},
    )


def sort_param(sort_by: list[dict[str, Any]] | None) -> str:
    """Convertit le `sort_by` de la DataTable en paramètre d'API (`field` ou `-field`)."""
    if not sort_by:
        return "id"
    column = sort_by[0]
    field = column["column_id"]
    return f"-{field}" if column.get("direction") == "desc" else field


def trajet_detail(detail: dict[str, Any]) -> html.Div:
    """Panneau de détail d'un trajet."""
    dep = detail.get("departure_station") or detail.get("departure_city")
    arr = detail.get("arrival_station") or detail.get("arrival_city")
    fields = [
        ("Opérateur", detail.get("agency_name")),
        ("Ligne", detail.get("route_long_name") or detail.get("route_short_name")),
        ("Départ", f"{dep} — {detail.get('departure_time')}"),
        ("Arrivée", f"{arr} — {detail.get('arrival_time')}"),
        ("Distance", f"{detail.get('distance_km')} km"),
        ("Nuit", "Oui" if detail.get("is_night_train") else "Non"),
        ("CO₂ / pkm", detail.get("co2_per_pkm")),
        ("Émissions", f"{detail.get('emissions_co2')} g"),
        ("Service", f"{detail.get('service_start_date')} → {detail.get('service_end_date')}"),
        ("Jours", detail.get("days_of_week")),
    ]
    return html.Div(
        className="detail",
        children=[
            html.H4(f"Trajet {detail.get('trip_id') or detail.get('id')}"),
            html.Dl([html.Div([html.Dt(label), html.Dd(str(value))]) for label, value in fields]),
        ],
    )
