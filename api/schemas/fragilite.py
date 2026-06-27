"""DTO de l'onglet « Fragilité territoriale » (V7)."""

from pydantic import BaseModel

from schemas.liaison import GeoPoint


class ClusterGeoPoint(BaseModel):
    """V7.1 — commune géolocalisée et son cluster de fragilité."""

    citycode: str | None
    city_name: str
    geo: GeoPoint
    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None


class ClusterSummary(BaseModel):
    """V7.4 — effectif d'un cluster (point d'entrée vers les profils)."""

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
    """V7.2 — profil multivarié d'un cluster (coordonnées parallèles)."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None
    effectif: int
    features: list[FeatureProfile]
