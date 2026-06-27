"""Onglet « Fragilité territoriale » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.cluster_client import ClusterClient
from components.charts import cluster_effectifs_bars, cluster_profils_parallel, clusters_map


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callback)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Fragilité territoriale"),
            dcc.Interval(id="fragilite-trigger", interval=200, max_intervals=1),
            dcc.Loading(dcc.Graph(id="clusters-map")),
            html.Div(
                className="charts-row",
                children=[
                    dcc.Graph(id="clusters-effectifs"),
                    dcc.Graph(id="clusters-profils"),
                ],
            ),
        ],
    )


def register_callbacks(app: Dash, client: ClusterClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("clusters-map", "figure"),
        Output("clusters-effectifs", "figure"),
        Output("clusters-profils", "figure"),
        Input("fragilite-trigger", "n_intervals"),
    )
    def _load(_n_intervals: int | None) -> tuple[Any, Any, Any]:
        try:
            carte = client.get_carte()
            summaries = client.get_summaries()
            profils = client.get_profils()
        except Exception:
            return {}, {}, {}
        return (
            clusters_map(carte),
            cluster_effectifs_bars(summaries),
            cluster_profils_parallel(profils),
        )
