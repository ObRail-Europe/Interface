"""Composants du simulateur de fragilité (V7.5) : formulaire + résultat (sans I/O)."""

from typing import Any

from dash import dcc, html

# (id, libellé, valeur par défaut, pas) - entrées brutes du modèle live.
SIMULATOR_FIELDS = [
    ("sim-population", "Population", 20000, 100),
    ("sim-densite_pop_km2", "Densité (hab/km²)", 500, 10),
    ("sim-part_65plus", "Part des 65 ans +", 0.2, 0.01),
    ("sim-revenu_median_uc", "Revenu médian (€/UC)", 22000, 500),
    ("sim-nb_lignes_total", "Nb de lignes", 2, 1),
    ("sim-nb_trajets_moy_arret", "Trajets moy./arrêt", 50, 10),
    ("sim-amplitude_moy_h", "Amplitude service (h)", 16, 1),
    ("sim-taux_sans_voiture", "Taux sans voiture", 0.15, 0.01),
    ("sim-distance_dom_trav_med_km", "Distance domicile-travail (km)", 10, 1),
    ("sim-dist_gare_min_m", "Distance à la gare (m)", 500, 50),
]

# id d'entrée -> nom de feature attendu par l'API.
FIELD_TO_FEATURE = {field_id: field_id.removeprefix("sim-") for field_id, *_ in SIMULATOR_FIELDS}


def _labeled_input(field_id: str, label: str, default: float, step: float) -> html.Div:
    return html.Div(
        className="sim-field",
        children=[
            html.Label(label, htmlFor=field_id),
            dcc.Input(id=field_id, type="number", value=default, step=step, debounce=True),
        ],
    )


def simulator_form() -> html.Div:
    """Formulaire de simulation : has_gare + entrées brutes + bouton de prédiction."""
    return html.Div(
        className="simulator",
        children=[
            html.H3("Simulateur de fragilité"),
            html.P(
                "Renseignez le profil d'un territoire pour estimer son cluster de fragilité "
                "(modèle live). Les champs vides sont imputés par la médiane.",
            ),
            html.Div(
                className="sim-field",
                children=[
                    html.Label("Présence d'une gare", htmlFor="sim-has_gare"),
                    dcc.Dropdown(
                        id="sim-has_gare",
                        options=[
                            {"label": "Avec gare", "value": "true"},
                            {"label": "Sans gare", "value": "false"},
                        ],
                        value="true",
                        clearable=False,
                    ),
                ],
            ),
            html.Div(
                className="sim-grid",
                children=[_labeled_input(*field) for field in SIMULATOR_FIELDS],
            ),
            html.Button("Prédire le cluster", id="sim-predict", n_clicks=0),
            dcc.Loading(html.Div(id="sim-result", role="status", **{"aria-live": "polite"})),
        ],
    )


def prediction_result(prediction: dict[str, Any]) -> html.Div:
    """Affiche le cluster prédit et son niveau de fragilité."""
    return html.Div(
        className="detail",
        children=[
            html.H4(f"Cluster {prediction['cluster']} - {prediction.get('cluster_nom') or ''}"),
            html.Dl(
                [
                    html.Div(
                        [html.Dt("Niveau de fragilité"), html.Dd(prediction["niveau_fragilite"])]
                    ),
                ]
            ),
        ],
    )
