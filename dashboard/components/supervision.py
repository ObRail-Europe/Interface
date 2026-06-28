"""Composants de l'onglet « Supervision » (V9.1) : badges d'état des services."""

from typing import Any

from dash import html


def _badge(service: dict[str, Any]) -> html.Div:
    up = service["statut"] == "up"
    return html.Div(
        className="health-card",
        children=[
            html.Div(service["nom"], className="health-name"),
            html.Div(
                "UP" if up else "DOWN",
                className=f"health-badge {'up' if up else 'down'}",
            ),
            html.Div(f"{service['latence_ms']:.0f} ms", className="health-latence"),
        ],
    )


def health_badges(details: dict[str, Any]) -> html.Div:
    """Bandeau de badges UP/DOWN par service (avec latence)."""
    services = details.get("services") or []
    return html.Div([_badge(service) for service in services], className="health-band")
