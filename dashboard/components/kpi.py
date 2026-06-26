"""Composant V1.1 : bandeau de KPI (fonction pure, sans I/O)."""

from typing import Any

from dash import html

_THIN_SPACE = " "


def _format_int(value: int) -> str:
    return f"{value:,}".replace(",", _THIN_SPACE)


def _card(label: str, value: str) -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(value, className="kpi-value"),
            html.Div(label, className="kpi-label"),
        ],
    )


def kpi_band(overview: dict[str, Any]) -> html.Div:
    """Construit le bandeau de 8 KPI à partir du DTO OverviewKPI."""
    distance = overview.get("distance_mediane_km") or 0
    cards = [
        _card("Trajets", _format_int(overview["total_trajets"])),
        _card("Part de nuit", f"{overview['part_nuit'] * 100:.0f}{_THIN_SPACE}%"),
        _card("Opérateurs", _format_int(overview["nb_operateurs"])),
        _card("Villes desservies", _format_int(overview["nb_villes_desservies"])),
        _card("Pays", _format_int(overview["nb_pays"])),
        _card("Transfrontalier", f"{overview['part_transfrontalier'] * 100:.0f}{_THIN_SPACE}%"),
        _card("Distance médiane", f"{distance:.0f}{_THIN_SPACE}km"),
        _card("CO₂ total", f"{overview['emissions_co2_totales_t']:.1f}{_THIN_SPACE}t"),
    ]
    return html.Div(cards, className="kpi-band")
