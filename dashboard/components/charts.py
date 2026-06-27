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


def departs_map(points: list[dict[str, Any]]) -> go.Figure:
    """Carte de chaleur des départs (V1.3) : couleur et taille ∝ volume de trajets."""
    counts = [point["nb_trajets"] for point in points]
    max_count = max(counts) if counts else 1
    fig = go.Figure(
        go.Scattergeo(
            lat=[point["lat"] for point in points],
            lon=[point["lon"] for point in points],
            text=[f"{point['city_name']} — {point['nb_trajets']} départs" for point in points],
            hoverinfo="text",
            marker={
                "color": counts,
                "colorscale": "YlOrRd",
                "showscale": True,
                "colorbar": {"title": "Départs"},
                "size": counts,
                "sizemode": "area",
                "sizeref": 2 * max_count / (35**2),
                "sizemin": 3,
            },
        )
    )
    fig.update_layout(
        title="Densité des départs",
        geo={
            "scope": "europe",
            "center": {"lat": 46.6, "lon": 2.4},
            "projection_scale": 4.5,
            "showcountries": True,
        },
        margin=_MARGIN,
    )
    return fig


def liaisons_map(liaisons: list[dict[str, Any]]) -> go.Figure:
    """Carte des liaisons origine→destination (V2.1).

    Les arcs sont regroupés en deux traces jour/nuit : c'est
    lisible et performant même avec un grand nombre de liaisons. Un point discret au
    milieu de chaque arc porte l'info au survol (départ → arrivée + nombre de trajets).
    """
    segments: dict[str, tuple[list[float | None], list[float | None]]] = {
        "jour": ([], []),
        "nuit": ([], []),
    }
    mid_lats: list[float] = []
    mid_lons: list[float] = []
    hovers: list[str] = []
    for liaison in liaisons:
        dep, arr = liaison["departure"], liaison["arrival"]
        lats, lons = segments["nuit" if liaison["part_nuit"] >= 0.5 else "jour"]
        lats += [dep["lat"], arr["lat"], None]
        lons += [dep["lon"], arr["lon"], None]
        mid_lats.append((dep["lat"] + arr["lat"]) / 2)
        mid_lons.append((dep["lon"] + arr["lon"]) / 2)
        hovers.append(
            f"{liaison['departure_city']} → {liaison['arrival_city']} : "
            f"{liaison['nb_trajets']} trajets"
        )

    fig = go.Figure()
    for key, color, opacity in (("jour", COLOR_JOUR, 0.35), ("nuit", COLOR_NUIT, 0.55)):
        lats, lons = segments[key]
        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                mode="lines",
                line={"width": 0.5, "color": color},
                opacity=opacity,
                name=key.capitalize(),
                hoverinfo="skip",
            )
        )
    # Points de survol au milieu des arcs.
    fig.add_trace(
        go.Scattergeo(
            lat=mid_lats,
            lon=mid_lons,
            text=hovers,
            mode="markers",
            marker={"size": 4, "color": "#5a6478", "opacity": 0.15},
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        title="Liaisons origine → destination",
        geo={
            "scope": "europe",
            "center": {"lat": 46.6, "lon": 2.4},
            "projection_scale": 4.5,
            "showcountries": True,
        },
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig
