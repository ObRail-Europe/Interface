"""Onglet « Explorateur de trajets » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.explorer_client import ExplorerClient
from components.charts import liaisons_map


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callback)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Explorateur de trajets"),
            dcc.Interval(id="explorer-trigger", interval=200, max_intervals=1),
            dcc.Loading(dcc.Graph(id="liaisons-map")),
        ],
    )


def register_callbacks(app: Dash, client: ExplorerClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(Output("liaisons-map", "figure"), Input("explorer-trigger", "n_intervals"))
    def _load_liaisons(_n_intervals: int | None) -> Any:
        try:
            liaisons = client.get_liaisons(100)
        except Exception:
            return {}
        return liaisons_map(liaisons)
