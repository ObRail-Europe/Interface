"""Onglet « Qualité des données » : layout et câblage des callbacks."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.qualite_client import QualiteClient
from components.charts import anomalies_bars, completude_bars, volumetrie_bars


def layout() -> html.Div:
    """Structure statique de la page (les données arrivent via callbacks)."""
    return html.Div(
        className="page",
        children=[
            html.H2("Qualité des données"),
            dcc.Interval(id="qualite-trigger", interval=200, max_intervals=1),
            html.Div(
                className="charts-row",
                children=[
                    dcc.Graph(id="qualite-anomalies"),
                    dcc.Graph(id="qualite-volumetrie"),
                ],
            ),
            html.H3("Complétude par colonne"),
            dcc.Dropdown(
                id="qualite-table",
                options=[
                    {"label": "Trajets", "value": "trajets"},
                    {"label": "Villes", "value": "villes"},
                    {"label": "Clusters", "value": "clusters"},
                ],
                value="trajets",
                clearable=False,
                className="filters",
            ),
            dcc.Loading(dcc.Graph(id="qualite-completude")),
        ],
    )


def register_callbacks(app: Dash, client: QualiteClient) -> None:
    """Branche les callbacks de la page sur le client fourni."""

    @app.callback(
        Output("qualite-anomalies", "figure"),
        Output("qualite-volumetrie", "figure"),
        Input("qualite-trigger", "n_intervals"),
    )
    def _load_overview(_n_intervals: int | None) -> tuple[Any, Any]:
        try:
            anomalies = client.get_anomalies()
            volumetrie = client.get_volumetrie()
        except Exception:
            return {}, {}
        return anomalies_bars(anomalies), volumetrie_bars(volumetrie)

    @app.callback(
        Output("qualite-completude", "figure"),
        Input("qualite-table", "value"),
    )
    def _load_completude(table: str | None) -> Any:
        try:
            completude = client.get_completude(table or "trajets")
        except Exception:
            return {}
        return completude_bars(completude)
