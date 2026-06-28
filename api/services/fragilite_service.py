"""Cas d'usage de l'onglet « Fragilité territoriale »."""

from repositories.interfaces import ClusterRepository
from schemas.fragilite import (
    ClusterGeoPoint,
    ClusterProfil,
    ClusterSummary,
    FeatureProfile,
    FragiliteMaille,
    FragiliteNiveau,
    FragiliteRepartition,
)
from schemas.liaison import GeoPoint

# Features profilées en coordonnées parallèles (V7.2), dans l'ordre d'affichage.
_PROFILE_FEATURES = (
    "revenu_median_uc",
    "taux_sans_voiture",
    "part_65plus",
    "densite_pop_km2",
    "nb_trajets_total",
    "dist_gare_min_m",
)

# Ordre croissant (inconnus rejetés en fin).
_NIVEAU_ORDER = ("Faible", "Faible-modérée", "Modérée", "Modérée-élevée", "Élevée")


def _niveau_rank(niveau: str) -> int:
    return _NIVEAU_ORDER.index(niveau) if niveau in _NIVEAU_ORDER else len(_NIVEAU_ORDER)


def _normalize(value: float | None, bounds: tuple[float, float] | None) -> float | None:
    """Min-max d'une moyenne dans l'intervalle inter-clusters (None si non calculable)."""
    if value is None or bounds is None:
        return None
    low, high = bounds
    return (value - low) / (high - low) if high > low else 0.0


class FragiliteService:
    """Construit les données de l'onglet fragilité à partir du repository."""

    def __init__(self, repository: ClusterRepository) -> None:
        self._repository = repository

    def get_carte(
        self,
        code_dept: str | None = None,
        code_region: str | None = None,
        has_gare: bool | None = None,
    ) -> list[ClusterGeoPoint]:
        """V7.1 — communes géolocalisées colorées par cluster de fragilité."""
        return [
            ClusterGeoPoint(
                citycode=c.citycode,
                city_name=c.city_name,
                geo=GeoPoint(lat=c.lat, lon=c.lon),
                cluster=c.cluster,
                cluster_nom=c.cluster_nom,
                niveau_fragilite=c.niveau_fragilite,
            )
            for c in self._repository.clusters_carte(code_dept, code_region, has_gare)
        ]

    def get_summaries(self) -> list[ClusterSummary]:
        """V7.4 — effectifs des clusters."""
        return [
            ClusterSummary(
                cluster=s.cluster,
                cluster_nom=s.cluster_nom,
                niveau_fragilite=s.niveau_fragilite,
                effectif=s.effectif,
            )
            for s in self._repository.cluster_summaries()
        ]

    def get_profils(self) -> list[ClusterProfil]:
        """V7.2 — profils des clusters (moyennes brutes + normalisées inter-clusters)."""
        profils = self._repository.cluster_profils(list(_PROFILE_FEATURES))
        bounds: dict[str, tuple[float, float] | None] = {}
        for name in _PROFILE_FEATURES:
            present = [p.feature_means.get(name) for p in profils]
            values = [v for v in present if v is not None]
            bounds[name] = (min(values), max(values)) if values else None

        return [
            ClusterProfil(
                cluster=p.cluster,
                cluster_nom=p.cluster_nom,
                niveau_fragilite=p.niveau_fragilite,
                effectif=p.effectif,
                features=[
                    FeatureProfile(
                        nom=name,
                        moyenne=p.feature_means.get(name),
                        moyenne_normalisee=_normalize(p.feature_means.get(name), bounds[name]),
                    )
                    for name in _PROFILE_FEATURES
                ],
            )
            for p in profils
        ]

    def get_repartition(self, by: str) -> FragiliteRepartition:
        """V7.3 — répartition des niveaux de fragilité par maille (ordonnée par gravité)."""
        mailles = []
        for m in self._repository.fragilite_par_maille(by):
            niveaux = sorted(m.repartition.items(), key=lambda kv: (_niveau_rank(kv[0]), kv[0]))
            mailles.append(
                FragiliteMaille(
                    cle=m.cle,
                    repartition=[FragiliteNiveau(niveau=n, nb=nb) for n, nb in niveaux],
                )
            )
        return FragiliteRepartition(by=by, mailles=mailles)
