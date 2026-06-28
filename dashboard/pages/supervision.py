"""Onglet « Supervision » : badges de santé (V9.1) + Grafana embarqué (V9.2/V9.3)."""

from typing import Any

from dash import Dash, Input, Output, dcc, html

from api.supervision_client import SupervisionClient
from components.supervision import health_badges
from config import settings

# Dashboard Grafana provisionné, embarqué en mode kiosk (métriques + journal).
_GRAFANA_EMBED = (
    f"{settings.grafana_url}/d/obrail-supervision/obrail-supervision?kiosk&theme=light&refresh=10s"
)


def layout() -> html.Div:
    """Structure statique : badges (rafraîchis) + iframe Grafana."""
    return html.Div(
        className="page",
        children=[
            html.H2("Supervision"),
            # Sonde de santé rafraîchie toutes les 10 s.
            dcc.Interval(id="supervision-trigger", interval=10_000),
            dcc.Loading(html.Div(id="supervision-health")),
            html.H3("Métriques & journal applicatif (Grafana)"),
            html.P(
                children=[
                    "Disponibilité, latence, taux d'erreurs et logs en temps réel — ",
                    html.A("ouvrir dans Grafana", href=_GRAFANA_EMBED, target="_blank"),
                    ".",
                ],
            ),
            html.Iframe(src=_GRAFANA_EMBED, className="grafana-embed"),
        ],
    )


def register_callbacks(app: Dash, client: SupervisionClient) -> None:
    """Branche la sonde de santé sur le client fourni."""

    @app.callback(
        Output("supervision-health", "children"),
        Input("supervision-trigger", "n_intervals"),
    )
    def _load_health(_n_intervals: int | None) -> Any:
        try:
            details = client.get_health_details()
        except Exception:
            # API injoignable → badge API DOWN.
            details = {"services": [{"nom": "api", "statut": "down", "latence_ms": 0}]}
        return health_badges(details)
