"""Onglet « Vue d'ensemble » : layout et câblage des callbacks.

Dépend de l'abstraction `OverviewClient` (injectée), pas d'une implémentation concrète.
"""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.client import OverviewClient
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
        ],
    )


def register_callbacks(app: Dash, client: OverviewClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(Output("overview-kpi", "children"), Input("overview-trigger", "n_intervals"))
    def _load_kpi(_n_intervals: int | None) -> Any:
        try:
            overview = client.get_overview()
        except Exception as exc:  # garde-fou UI : ne pas planter si l'API est indisponible
            return html.Div(f"Données indisponibles : {exc}", className="error")
        return kpi_band(overview)
