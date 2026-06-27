"""Onglet « Empreinte carbone » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.carbon_client import CarbonClient
from components.carbon import co2_counter
from components.charts import carbon_density_scatter, comparaison_avion_bars


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callback)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Empreinte carbone — train vs avion"),
            dcc.Interval(id="carbon-trigger", interval=200, max_intervals=1),
            dcc.Loading(html.Div(id="co2-counter")),
            dcc.Loading(dcc.Graph(id="co2-comparaison")),
            dcc.Loading(dcc.Graph(id="co2-density")),
        ],
    )


def register_callbacks(app: Dash, client: CarbonClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("co2-counter", "children"),
        Output("co2-comparaison", "figure"),
        Input("carbon-trigger", "n_intervals"),
    )
    def _load_comparaison(_n_intervals: int | None) -> tuple[Any, Any]:
        try:
            comparaison = client.get_comparaison()
        except Exception as exc:
            return html.Div(f"Données indisponibles : {exc}", className="error"), {}
        return co2_counter(comparaison), comparaison_avion_bars(comparaison)

    @app.callback(
        Output("co2-density", "figure"),
        Input("carbon-trigger", "n_intervals"),
    )
    def _load_density(_n_intervals: int | None) -> Any:
        try:
            density = client.get_density()
        except Exception:
            return {}
        return carbon_density_scatter(density)
