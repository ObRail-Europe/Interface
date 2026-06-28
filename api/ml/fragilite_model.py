"""Inférence live du modèle de fragilité territoriale.

Le modèle (`cluster_fragilite.joblib`) est un **KMeans stratifié par `has_gare`** : ses
centroïdes vivent dans l'espace des 9 features transformées. `preprocessing.joblib` porte
les paramètres pour passer des **entrées brutes** à ces features :
imputation (médianes), dérivation, winsorisation (bornes IQR) puis `log1p`.

La prédiction reproduit la partition d'origine à ~99,98 % (validé contre la table
`clusters`). Les artefacts sont des dicts numpy purs.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

_MODEL_FILE = "cluster_fragilite.joblib"
_PREPROCESSING_FILE = "preprocessing.joblib"

_NON_LOG_FEATURE = "part_65plus"

_FALLBACK_DEFAULTS = {"population": 1.0}


@dataclass(frozen=True)
class FragilitePredictionResult:
    """Cluster prédit et ses libellés."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None


class FragiliteModel:
    """Encapsule la chaîne préprocessing -> plus-proche-centroïde stratifié par `has_gare`."""

    def __init__(self, model: Mapping[str, Any], preprocessing: Mapping[str, Any]) -> None:
        self._cluster_nom = dict(model["cluster_nom"])
        self._fragilite = dict(model["fragilite"])
        self._with_gare = [int(c) for c in model["clusters_with_gare"]]
        self._without_gare = [int(c) for c in model["clusters_without_gare"]]
        self._centroids = {
            int(k): np.asarray(v, dtype=float) for k, v in model["centroids"].items()
        }

        self._raw_inputs = list(preprocessing["raw_inputs"])
        self._features = list(preprocessing["features"])
        self._winsor = dict(preprocessing["winsor_bounds"])
        self._medians = dict(preprocessing["impute_median_values"])
        self._log_features = {f for f in self._features if f != _NON_LOG_FEATURE}

    @property
    def raw_inputs(self) -> list[str]:
        """Colonnes brutes attendues en entrée (hors `has_gare`)."""
        return list(self._raw_inputs)

    def predict(self, raw: Mapping[str, float | None], has_gare: bool) -> FragilitePredictionResult:
        """Affecte la commune (features brutes + `has_gare`) à son cluster le plus proche."""
        vector = self._feature_vector(raw, has_gare)
        stratum = self._with_gare if has_gare else self._without_gare
        cluster = min(stratum, key=lambda c: float(np.linalg.norm(vector - self._centroids[c])))
        return FragilitePredictionResult(
            cluster=cluster,
            cluster_nom=self._cluster_nom.get(cluster),
            niveau_fragilite=self._fragilite.get(cluster),
        )

    def _impute(self, raw: Mapping[str, float | None], name: str) -> float:
        value = raw.get(name)
        if value is not None:
            return float(value)
        return float(self._medians.get(name, _FALLBACK_DEFAULTS.get(name, 0.0)))

    def _feature_vector(self, raw: Mapping[str, float | None], has_gare: bool) -> np.ndarray:
        # Features dérivées des entrées brutes (cf. preprocessing.joblib).
        dist_gare = self._impute(raw, "dist_gare_min_m")
        values = {
            "dist_gare_corrected": 0.0 if has_gare else dist_gare,
            "stress_mobilite": self._impute(raw, "taux_sans_voiture")
            * self._impute(raw, "distance_dom_trav_med_km"),
            "nb_lignes_total": self._impute(raw, "nb_lignes_total"),
            "nb_trajets_moy_arret": self._impute(raw, "nb_trajets_moy_arret"),
            "amplitude_moy_h": self._impute(raw, "amplitude_moy_h"),
            "densite_pop_km2": self._impute(raw, "densite_pop_km2"),
            "population": self._impute(raw, "population"),
            "part_65plus": self._impute(raw, "part_65plus"),
            "revenu_median_uc": self._impute(raw, "revenu_median_uc"),
        }
        components = []
        for feature in self._features:
            low, high = self._winsor[feature]
            x = min(max(values[feature], low), high)  # winsorisation (bornes IQR)
            if feature in self._log_features:
                x = math.log1p(max(x, 0.0))
            components.append(x)
        return np.asarray(components, dtype=float)


def load_fragilite_model(model_dir: str) -> FragiliteModel:
    """Charge les artefacts depuis `model_dir` (lève FileNotFoundError s'ils sont absents)."""
    directory = Path(model_dir)
    model = joblib.load(directory / _MODEL_FILE)
    preprocessing = joblib.load(directory / _PREPROCESSING_FILE)
    return FragiliteModel(model, preprocessing)
