"""Onglet « Explorateur de trajets » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.explorer_client import ExplorerClient
from components.charts import distance_histogram, liaisons_map
from components.tables import filter_controls, sort_param, trajets_table

_NIGHT_TO_FILTER = {"jour": "false", "nuit": "true"}


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callbacks)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Explorateur de trajets"),
            dcc.Interval(id="explorer-trigger", interval=200, max_intervals=1),
            dcc.Loading(dcc.Graph(id="liaisons-map")),
            dcc.Loading(dcc.Graph(id="distance-hist")),
            html.H3("Trajets"),
            filter_controls(),
            trajets_table(),
        ],
    )


def register_callbacks(app: Dash, client: ExplorerClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("liaisons-map", "figure"),
        Output("distance-hist", "figure"),
        Input("explorer-trigger", "n_intervals"),
    )
    def _load_charts(_n_intervals: int | None) -> tuple[Any, Any]:
        try:
            liaisons = client.get_liaisons(1000)
            histogram = client.get_distance_histogram(100)
        except Exception:
            return {}, {}
        return liaisons_map(liaisons), distance_histogram(histogram)

    @app.callback(
        Output("trajets-table", "data"),
        Output("trajets-table", "page_count"),
        Input("trajets-table", "page_current"),
        Input("trajets-table", "page_size"),
        Input("trajets-table", "sort_by"),
        Input("f-mode", "value"),
        Input("f-night", "value"),
        Input("f-dep-city", "value"),
        Input("f-arr-city", "value"),
        Input("f-agency", "value"),
    )
    def _load_table(
        page_current: int | None,
        page_size: int | None,
        sort_by: list[dict[str, Any]] | None,
        mode: str | None,
        night: str | None,
        dep_city: str | None,
        arr_city: str | None,
        agency: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = {
            "mode": mode,
            "is_night": _NIGHT_TO_FILTER.get(night or ""),
            "departure_city": dep_city,
            "arrival_city": arr_city,
            "agency_name": agency,
        }
        try:
            result = client.list_trajets(
                filters, sort_param(sort_by), (page_current or 0) + 1, page_size or 20
            )
        except Exception:
            return [], 0
        return result["items"], result["pages"]
