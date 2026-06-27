"""Composant compteur de l'onglet « Empreinte carbone » (fonction pure, sans I/O)."""

from typing import Any

from dash import html

_THIN_SPACE = " "


def _format_tonnes(tonnes: float) -> str:
    """Formate une masse de CO₂ (tonnes) avec l'unité la plus lisible (t / kt / Mt)."""
    if abs(tonnes) >= 1_000_000:
        return f"{tonnes / 1_000_000:.1f}{_THIN_SPACE}Mt"
    if abs(tonnes) >= 1_000:
        return f"{tonnes / 1_000:.1f}{_THIN_SPACE}kt"
    return f"{tonnes:.1f}{_THIN_SPACE}t"


def _card(label: str, value: str, *, hero: bool = False) -> html.Div:
    class_name = "kpi-card kpi-hero" if hero else "kpi-card"
    return html.Div(
        className=class_name,
        children=[
            html.Div(value, className="kpi-value"),
            html.Div(label, className="kpi-label"),
        ],
    )


def co2_counter(comparaison: dict[str, Any]) -> html.Div:
    """Compteur « CO₂ évité vs avion » (V5.1) : callout + contexte (facteur affiché)."""
    facteur = comparaison["facteur_avion_g_par_pkm"]
    cards = [
        _card("CO₂ évité vs avion", _format_tonnes(comparaison["co2_evite_t"]), hero=True),
        _card("Émissions réelles (train)", _format_tonnes(comparaison["co2_train_total_t"])),
        _card("Estimation si avion", _format_tonnes(comparaison["co2_avion_estime_t"])),
        _card("Facteur avion retenu", f"{facteur:.0f}{_THIN_SPACE}g/pkm"),
    ]
    return html.Div(cards, className="kpi-band")
