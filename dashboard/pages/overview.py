"""Onglet « Vue d'ensemble » : layout et câblage des callbacks.

Dépend de l'abstraction `OverviewClient` (injectée), pas d'une implémentation concrète.
"""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.client import OverviewClient
from components.charts import jour_nuit_donut, operateurs_bar
from components.kpi import kpi_band


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callback)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Vue d'ensemble"),
            # Déclenche un unique chargement au montage de la page.
            dcc.Interval(id="overview-trigger", interval=200, max_intervals=1),
            dcc.Loading(html.Div(id="overview-kpi")),
            html.Div(
                className="charts-row",
                children=[
                    dcc.Graph(id="jour-nuit-donut"),
                    dcc.Graph(id="operateurs-bar"),
                ],
            ),
        ],
    )


def register_callbacks(app: Dash, client: OverviewClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("overview-kpi", "children"),
        Output("jour-nuit-donut", "figure"),
        Output("operateurs-bar", "figure"),
        Input("overview-trigger", "n_intervals"),
    )
    def _load_overview(_n_intervals: int | None) -> tuple[Any, Any, Any]:
        try:
            overview = client.get_overview()
            split = client.get_jour_nuit()
            operateurs = client.get_operateurs(5)
        except Exception as exc:  # garde-fou UI : ne pas planter si l'API est indisponible
            error = html.Div(f"Données indisponibles : {exc}", className="error")
            return error, {}, {}
        return kpi_band(overview), jour_nuit_donut(split), operateurs_bar(operateurs)
