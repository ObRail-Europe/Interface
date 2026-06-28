"""Composants graphiques du dashboard (fonctions pures → figure Plotly)."""

from typing import Any

import plotly.graph_objects as go

from theme import (
    COLOR_AVION,
    COLOR_CLUSTERS,
    COLOR_FRAGILITE,
    COLOR_JOUR,
    COLOR_NUIT,
    COLOR_TRAIN,
)

_FRAGILITE_ORDER = ("Faible", "Faible-modérée", "Modérée", "Modérée-élevée", "Élevée")

_MARGIN = {"t": 50, "b": 10, "l": 10, "r": 10}

_GEO_EUROPE = {
    "scope": "europe",
    "center": {"lat": 46.6, "lon": 2.4},
    "projection_scale": 4.5,
    "showcountries": True,
}

# Couleurs des sévérités d'anomalies (onglet Qualité).
_SEVERITE_COLORS = {"info": "#3b82f6", "warn": "#e8a33d", "error": "#c0392b"}


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
    # Valeur ramenée en milliers (lisibilité de la colorbar)
    valeurs = [(point["valeur"] or 0) / 1000 for point in points]
    fig = go.Figure(
        go.Scattergeo(
            lat=[point["geo"]["lat"] for point in points],
            lon=[point["geo"]["lon"] for point in points],
            text=[
                f"{point['city_name']} — {dimension_label} : {valeur:.2f}"
                for point, valeur in zip(points, valeurs, strict=True)
            ],
            hoverinfo="text",
            marker={
                "color": valeurs,
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


def couverture_bars(couverture: dict[str, Any], limit: int = 20) -> go.Figure:
    """Couverture par maille (V6.2) : barres triées par desserte, couleur = taux de gare."""
    rows = list(reversed(couverture["mailles"][:limit]))  # mieux desservi en haut
    maille = "région" if couverture["by"] == "code_region" else "département"
    fig = go.Figure(
        go.Bar(
            x=[m["nb_trajets_total"] for m in rows],
            y=[m["cle"] for m in rows],
            orientation="h",
            marker={
                "color": [m["taux_avec_gare"] for m in rows],
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Taux gare"},
                "cmin": 0,
                "cmax": 1,
            },
            customdata=[[m["nb_communes"], m["taux_avec_gare"]] for m in rows],
            hovertemplate=(
                "%{y} — %{x} trajets · %{customdata[0]} communes · "
                "gare %{customdata[1]:.0%}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"Desserte par {maille} (top {limit})",
        xaxis_title="Trajets desservis",
        yaxis_title=maille.capitalize(),
        margin=_MARGIN,
    )
    return fig


def amplitude_hist(distribution: dict[str, Any]) -> go.Figure:
    """Distribution de l'amplitude de service (V6.4) ; part desservie après minuit en sous-titre."""
    bins = distribution["bins"]
    part = distribution["part_apres_minuit"]
    fig = go.Figure(
        go.Bar(
            x=[b["min_h"] for b in bins],
            y=[b["nb_communes"] for b in bins],
            marker_color=COLOR_NUIT,
            hovertemplate="%{x}–%{customdata} h : %{y} communes<extra></extra>",
            customdata=[b["max_h"] for b in bins],
        )
    )
    fig.update_layout(
        title=f"Amplitude de service · {part:.0%} des communes desservies après minuit",
        xaxis_title="Amplitude moyenne (h)",
        yaxis_title="Communes",
        margin=_MARGIN,
    )
    return fig


def _cluster_color(cluster: int) -> str:
    return COLOR_CLUSTERS[cluster % len(COLOR_CLUSTERS)]


def clusters_map(points: list[dict[str, Any]]) -> go.Figure:
    """Carte des clusters de fragilité (V7.1) : une trace par cluster (couleur + légende)."""
    by_cluster: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for point in points:
        key = (point["cluster"], point["cluster_nom"] or f"cluster {point['cluster']}")
        by_cluster.setdefault(key, []).append(point)

    fig = go.Figure()
    for cluster, nom in sorted(by_cluster):
        pts = by_cluster[(cluster, nom)]
        fig.add_trace(
            go.Scattergeo(
                lat=[p["geo"]["lat"] for p in pts],
                lon=[p["geo"]["lon"] for p in pts],
                text=[f"{p['city_name']} — {nom} ({p['niveau_fragilite']})" for p in pts],
                hoverinfo="text",
                mode="markers",
                name=nom,
                marker={"size": 5, "color": _cluster_color(cluster), "opacity": 0.6},
            )
        )
    fig.update_layout(
        title="Clusters de fragilité territoriale",
        geo=_GEO_EUROPE,
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig


def cluster_effectifs_bars(summaries: list[dict[str, Any]]) -> go.Figure:
    """Effectifs des clusters (V7.4) : barres horizontales, couleur par cluster."""
    rows = list(reversed(summaries))
    fig = go.Figure(
        go.Bar(
            x=[s["effectif"] for s in rows],
            y=[s["cluster_nom"] or f"cluster {s['cluster']}" for s in rows],
            orientation="h",
            marker_color=[_cluster_color(s["cluster"]) for s in rows],
            customdata=[s["niveau_fragilite"] for s in rows],
            hovertemplate="%{y} — %{x} communes · fragilité %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Effectifs des clusters",
        xaxis_title="Communes",
        margin=_MARGIN,
    )
    return fig


# Libellés courts et lisibles des features de profil (axes des coordonnées parallèles).
_FEATURE_LABELS = {
    "revenu_median_uc": "Revenu",
    "taux_sans_voiture": "Sans voiture",
    "part_65plus": "65 ans +",
    "densite_pop_km2": "Densité",
    "nb_trajets_total": "Trajets",
    "dist_gare_min_m": "Dist. gare",
}


def fragilite_stacked_bars(repartition: dict[str, Any]) -> go.Figure:
    """Répartition de la fragilité par maille (V7.3) : barres empilées par niveau."""
    mailles = repartition["mailles"]
    cles = [m["cle"] for m in mailles]
    counts = [{r["niveau"]: r["nb"] for r in m["repartition"]} for m in mailles]
    present = [n for n in _FRAGILITE_ORDER if any(n in c for c in counts)]

    fig = go.Figure()
    for niveau in present:
        fig.add_trace(
            go.Bar(
                x=cles,
                y=[c.get(niveau, 0) for c in counts],
                name=niveau,
                marker_color=COLOR_FRAGILITE.get(niveau),
            )
        )
    fig.update_layout(
        barmode="stack",
        title=f"Répartition de la fragilité par {repartition['by'].removeprefix('code_')}",
        xaxis_title=repartition["by"].removeprefix("code_").capitalize(),
        yaxis_title="Communes",
        margin=_MARGIN,
        legend={"orientation": "h"},
    )
    return fig


def cluster_profils_parallel(profils: list[dict[str, Any]]) -> go.Figure:
    """Profils des clusters (V7.2) : coordonnées parallèles des features normalisées 0–1."""
    if not profils:
        return go.Figure()
    names = [f["nom"] for f in profils[0]["features"]]
    # Ne garder que les features renseignées.
    kept = [
        i
        for i, _ in enumerate(names)
        if any(p["features"][i]["moyenne_normalisee"] is not None for p in profils)
    ]
    dimensions = [
        {
            "label": _FEATURE_LABELS.get(names[i], names[i]),
            "range": [0, 1],
            "values": [(p["features"][i]["moyenne_normalisee"] or 0) for p in profils],
        }
        for i in kept
    ]
    fig = go.Figure(
        go.Parcoords(
            line={
                "color": [p["cluster"] for p in profils],
                "colorscale": "Viridis",
                "showscale": True,
                "colorbar": {"title": "Cluster"},
            },
            dimensions=dimensions,
            labelangle=0,
        )
    )
    # Marge haute généreuse : sépare le titre des libellés d'axes (sinon ils se chevauchent).
    fig.update_layout(
        title={"text": "Profils des clusters (features normalisées 0–1)", "y": 0.98},
        margin={"t": 90, "b": 40, "l": 70, "r": 70},
    )
    return fig


def completude_bars(completude: dict[str, Any]) -> go.Figure:
    """Complétude par colonne (V8.1) : barres horizontales (rouge = lacunaire → vert = complet)."""
    colonnes = list(reversed(completude["colonnes"]))
    taux = [c["taux_complet"] for c in colonnes]
    fig = go.Figure(
        go.Bar(
            x=[t * 100 for t in taux],
            y=[c["nom"] for c in colonnes],
            orientation="h",
            marker={"color": taux, "colorscale": "RdYlGn", "cmin": 0, "cmax": 1},
            customdata=[c["nb_nuls"] for c in colonnes],
            hovertemplate="%{y} — %{x:.1f} % complet · %{customdata} NULLs<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Complétude — {completude['table']} ({completude['nb_lignes']} lignes)",
        xaxis_title="Complétude (%)",
        xaxis={"range": [0, 100]},
        margin={"t": 50, "b": 30, "l": 10, "r": 10},
        height=max(300, 22 * len(colonnes)),
    )
    return fig


def anomalies_bars(anomalies: dict[str, Any]) -> go.Figure:
    """Anomalies & doublons (V8.2) : barres horizontales colorées par sévérité."""
    rows = list(reversed(anomalies["anomalies"]))
    fig = go.Figure(
        go.Bar(
            x=[a["nb"] for a in rows],
            y=[a["libelle"] for a in rows],
            orientation="h",
            marker_color=[_SEVERITE_COLORS.get(a["severite"], "#999") for a in rows],
            customdata=[a["severite"] for a in rows],
            hovertemplate="%{y} — %{x} (%{customdata})<extra></extra>",
        )
    )
    fig.update_layout(
        title="Anomalies & doublons",
        xaxis_title="Occurrences",
        margin={"t": 50, "b": 30, "l": 10, "r": 10},
    )
    return fig


def volumetrie_bars(volumetrie: dict[str, Any], limit: int = 15) -> go.Figure:
    """Volumétrie par source (V8.4) : barres horizontales des plus gros volumes."""
    rows = list(reversed(volumetrie["sources"][:limit]))
    fig = go.Figure(
        go.Bar(
            x=[s["nb"] for s in rows],
            y=[s["cle"] for s in rows],
            orientation="h",
            marker_color=COLOR_NUIT,
        )
    )
    fig.update_layout(
        title=f"Volumétrie par source (top {limit})",
        xaxis_title="Trajets",
        margin={"t": 50, "b": 30, "l": 10, "r": 10},
    )
    return fig
