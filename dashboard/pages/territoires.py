"""Onglet « Territoires & couverture ferroviaire » : layout et callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.territoire_client import TerritoireClient
from components.charts import couverture_bars, couverture_map

_DIMENSIONS = {
    "nb_trajets_total": "Trajets desservis",
    "has_gare": "Présence d'une gare",
    "accessibilite_ord": "Accessibilité",
    "dist_gare_min_m": "Distance à la gare (km)",
}

_MAILLES = {"code_dept": "Département", "code_region": "Région"}


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callback)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Territoires & couverture ferroviaire"),
            html.Div(
                className="filters",
                children=[
                    dcc.Dropdown(
                        id="terr-dimension",
                        options=[
                            {"label": label, "value": key} for key, label in _DIMENSIONS.items()
                        ],
                        value="nb_trajets_total",
                        clearable=False,
                    ),
                ],
            ),
            dcc.Loading(dcc.Graph(id="couverture-map")),
            html.H3("Couverture par territoire"),
            html.Div(
                className="filters",
                children=[
                    dcc.Dropdown(
                        id="terr-maille",
                        options=[{"label": label, "value": key} for key, label in _MAILLES.items()],
                        value="code_dept",
                        clearable=False,
                    ),
                ],
            ),
            dcc.Loading(dcc.Graph(id="couverture-bars")),
        ],
    )


def register_callbacks(app: Dash, client: TerritoireClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("couverture-map", "figure"),
        Input("terr-dimension", "value"),
    )
    def _load_map(dimension: str | None) -> Any:
        dimension = dimension or "nb_trajets_total"
        try:
            points = client.get_carte(dimension)
        except Exception:
            return {}
        return couverture_map(points, _DIMENSIONS.get(dimension, dimension))

    @app.callback(
        Output("couverture-bars", "figure"),
        Input("terr-maille", "value"),
    )
    def _load_couverture(maille: str | None) -> Any:
        try:
            couverture = client.get_couverture(maille or "code_dept")
        except Exception:
            return {}
        return couverture_bars(couverture)
