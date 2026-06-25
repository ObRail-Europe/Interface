"""Composants graphiques de l'onglet Vue d'ensemble (fonctions pures → figure Plotly)."""

from typing import Any

import plotly.graph_objects as go

from theme import COLOR_JOUR, COLOR_NUIT

_MARGIN = {"t": 50, "b": 10, "l": 10, "r": 10}


def jour_nuit_donut(split: dict[str, Any]) -> go.Figure:
    """Donut jour vs nuit (V1.2), part de nuit au centre."""
    part_nuit = split["nuit"]["part"]
    fig = go.Figure(
        go.Pie(
            labels=["Jour", "Nuit"],
            values=[split["jour"]["nb_trajets"], split["nuit"]["nb_trajets"]],
            hole=0.6,
            sort=False,
            marker={"colors": [COLOR_JOUR, COLOR_NUIT]},
        )
    )
    fig.update_layout(
        title="Répartition jour / nuit",
        annotations=[{"text": f"{part_nuit * 100:.0f} %<br>nuit", "showarrow": False}],
        margin=_MARGIN,
    )
    return fig


def operateurs_bar(operateurs: list[dict[str, Any]]) -> go.Figure:
    """Top opérateurs en barres horizontales (V1.4), plus gros volume en haut."""
    rows = list(reversed(operateurs))
    fig = go.Figure(
        go.Bar(
            x=[op["nb_trajets"] for op in rows],
            y=[op["agency_name"] for op in rows],
            orientation="h",
            marker_color=COLOR_NUIT,
        )
    )
    fig.update_layout(title="Top opérateurs", xaxis_title="Trajets", margin=_MARGIN)
    return fig
