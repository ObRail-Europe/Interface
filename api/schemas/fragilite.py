"""DTO de l'onglet « Fragilité territoriale » (V7)."""

from pydantic import BaseModel

from schemas.liaison import GeoPoint


class ClusterGeoPoint(BaseModel):
    """V7.1 - commune géolocalisée et son cluster de fragilité."""

    citycode: str | None
    city_name: str
    geo: GeoPoint
    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None


class ClusterSummary(BaseModel):
    """V7.4 - effectif d'un cluster (point d'entrée vers les profils)."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None
    effectif: int


class FeatureProfile(BaseModel):
    """Moyenne d'une feature pour un cluster (brute + normalisée 0..1 inter-clusters)."""

    nom: str
    moyenne: float | None
    moyenne_normalisee: float | None


class ClusterProfil(BaseModel):
    """V7.2 - profil multivarié d'un cluster (coordonnées parallèles)."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None
    effectif: int
    features: list[FeatureProfile]


class FragiliteFeatures(BaseModel):
    """V7.5 - entrées brutes du simulateur (toutes optionnelles : imputées par médiane).

    `has_gare` n'est pas une feature mais la variable de **stratification** du modèle.
    """

    has_gare: bool
    population: float | None = None
    densite_pop_km2: float | None = None
    part_65plus: float | None = None
    revenu_median_uc: float | None = None
    nb_lignes_total: float | None = None
    nb_trajets_moy_arret: float | None = None
    amplitude_moy_h: float | None = None
    taux_sans_voiture: float | None = None
    distance_dom_trav_med_km: float | None = None
    dist_gare_min_m: float | None = None


class FragilitePrediction(BaseModel):
    """V7.5 - cluster prédit par le modèle live."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None


class FragiliteNiveau(BaseModel):
    """Effectif d'un niveau de fragilité dans une maille."""

    niveau: str
    nb: int


class FragiliteMaille(BaseModel):
    """V7.3 - répartition des niveaux de fragilité dans une maille."""

    cle: str
    repartition: list[FragiliteNiveau]


class FragiliteRepartition(BaseModel):
    """V7.3 - répartition de la fragilité par maille (barres empilées)."""

    by: str
    mailles: list[FragiliteMaille]
