"""Onglet « Fragilité territoriale » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, State, dcc, html

from api.cluster_client import ClusterClient
from components.charts import (
    cluster_effectifs_bars,
    cluster_profils_parallel,
    clusters_map,
    fragilite_stacked_bars,
)
from components.fragilite import (
    FIELD_TO_FEATURE,
    SIMULATOR_FIELDS,
    prediction_result,
    simulator_form,
)

_FIELD_IDS = [field_id for field_id, *_ in SIMULATOR_FIELDS]


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
            html.H3("Répartition de la fragilité par territoire"),
            dcc.Dropdown(
                id="fragilite-maille",
                options=[
                    {"label": "Par région", "value": "code_region"},
                    {"label": "Par département", "value": "code_dept"},
                ],
                value="code_region",
                clearable=False,
                className="filters",
            ),
            dcc.Loading(dcc.Graph(id="fragilite-repartition")),
            simulator_form(),
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

    @app.callback(
        Output("fragilite-repartition", "figure"),
        Input("fragilite-maille", "value"),
    )
    def _load_repartition(by: str | None) -> Any:
        try:
            repartition = client.get_repartition(by or "code_region")
        except Exception:
            return {}
        return fragilite_stacked_bars(repartition)

    @app.callback(
        Output("sim-result", "children"),
        Input("sim-predict", "n_clicks"),
        [State("sim-has_gare", "value"), *[State(fid, "value") for fid in _FIELD_IDS]],
        prevent_initial_call=True,
    )
    def _predict(_n_clicks: int, has_gare: str, *values: float | None) -> Any:
        features: dict[str, Any] = {"has_gare": has_gare == "true"}
        for field_id, value in zip(_FIELD_IDS, values, strict=True):
            features[FIELD_TO_FEATURE[field_id]] = value
        try:
            prediction = client.predict(features)
        except Exception:
            return html.Div("Prédiction indisponible", className="error")
        return prediction_result(prediction)
