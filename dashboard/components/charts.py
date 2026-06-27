"""Composants graphiques du dashboard (fonctions pures → figure Plotly)."""

from typing import Any

import plotly.graph_objects as go

from theme import COLOR_AVION, COLOR_JOUR, COLOR_NUIT, COLOR_TRAIN

_MARGIN = {"t": 50, "b": 10, "l": 10, "r": 10}

_GEO_EUROPE = {
    "scope": "europe",
    "center": {"lat": 46.6, "lon": 2.4},
    "projection_scale": 4.5,
    "showcountries": True,
}


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


def comparaison_avion_bars(comparaison: dict[str, Any]) -> go.Figure:
    """Barres comparées train réel vs estimation avion, par tranche de distance (V5.1)."""
    tranches = comparaison["par_tranche"]
    labels = [f"{int(t['min_km'])}–{int(t['max_km'])}" for t in tranches]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[t["train_t"] for t in tranches],
            name="Train (réel)",
            marker_color=COLOR_TRAIN,
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[t["avion_t"] for t in tranches],
            name="Avion (estimé)",
            marker_color=COLOR_AVION,
        )
    )
    fig.update_layout(
        barmode="group",
        title="CO₂ : train réel vs estimation avion, par distance",
        xaxis_title="Distance (km)",
        yaxis_title="CO₂ (t)",
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig


def carbon_density_scatter(density: dict[str, Any]) -> go.Figure:
    """Densité distance × intensité carbone (V5.2) : une bulle par cellule, colorée par mode.

    La taille des bulles encode le nombre de trajets ; les deux modes forment des nuages
    distincts (le train à basse intensité, l'avion bien plus haut).
    """
    bins = density["bins"]
    max_count = max((b["count"] for b in bins), default=1)
    fig = go.Figure()
    for mode, color, label in (("train", COLOR_TRAIN, "Train"), ("flight", COLOR_AVION, "Avion")):
        cells = [b for b in bins if b["mode"] == mode]
        hover = f"{label} — %{{x}} km · %{{y}} g/pkm : %{{customdata}} trajets<extra></extra>"
        fig.add_trace(
            go.Scatter(
                x=[c["x_km"] for c in cells],
                y=[c["y_co2_pkm"] for c in cells],
                customdata=[c["count"] for c in cells],
                mode="markers",
                name=label,
                marker={
                    "color": color,
                    "size": [c["count"] for c in cells],
                    "sizemode": "area",
                    "sizeref": 2 * max_count / (30**2),
                    "sizemin": 3,
                    "opacity": 0.5,
                },
                hovertemplate=hover,
            )
        )
    fig.update_layout(
        title="Distance × intensité carbone (densité)",
        xaxis_title="Distance (km)",
        yaxis_title="CO₂ (g/pkm)",
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig


def co2_distribution_box(distribution: dict[str, Any]) -> go.Figure:
    """Box plot du CO₂/pkm par mode (V5.3), à partir des quartiles précalculés."""
    colors = {"train": COLOR_TRAIN, "flight": COLOR_AVION}
    labels = {"train": "Train", "flight": "Avion"}
    fig = go.Figure()
    for mode in distribution["modes"]:
        key = mode["mode"]
        label = labels.get(key, key)
        fig.add_trace(
            go.Box(
                name=label,
                x=[label],  # une catégorie distincte par mode (sinon les box se superposent)
                q1=[mode["q1"]],
                median=[mode["mediane"]],
                q3=[mode["q3"]],
                lowerfence=[mode["min"]],
                upperfence=[mode["max"]],
                mean=[mode["moyenne"]],
                marker_color=colors.get(key),
            )
        )
    fig.update_layout(
        title="Distribution du CO₂/pkm par mode",
        yaxis_title="CO₂ (g/pkm)",
        margin=_MARGIN,
        showlegend=False,
    )
    return fig


def distance_histogram(histogram: dict[str, Any]) -> go.Figure:
    """Histogramme empilé des distances (V2.3), réparti jour/nuit."""
    bins = histogram["bins"]
    x = [b["min_km"] for b in bins]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=x, y=[b["count_jour"] for b in bins], name="Jour", marker_color=COLOR_JOUR)
    )
    fig.add_trace(
        go.Bar(x=x, y=[b["count_nuit"] for b in bins], name="Nuit", marker_color=COLOR_NUIT)
    )
    fig.update_layout(
        barmode="stack",
        title=f"Distribution des distances (pas {histogram['bin_km']} km)",
        xaxis_title="Distance (km)",
        yaxis_title="Trajets",
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig


def couverture_map(points: list[dict[str, Any]], dimension_label: str) -> go.Figure:
    """Carte de la couverture ferroviaire (V6.1) : couleur = dimension, taille ∝ population."""
    pops = [point["population"] or 0 for point in points]
    max_pop = max(pops) if pops else 1
    fig = go.Figure(
        go.Scattergeo(
            lat=[point["geo"]["lat"] for point in points],
            lon=[point["geo"]["lon"] for point in points],
            text=[
                f"{point['city_name']} — {dimension_label} : {point['valeur'] / 1000:.2f}" for point in points
            ],
            hoverinfo="text",
            marker={
                "color": [point["valeur"] / 1000 for point in points],
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": dimension_label},
                "size": pops,
                "sizemode": "area",
                "sizeref": 2 * max_pop / (30**2),
                "sizemin": 3,
            },
        )
    )
    fig.update_layout(
        title="Couverture ferroviaire des communes",
        geo=_GEO_EUROPE,
        margin=_MARGIN,
    )
    return fig
