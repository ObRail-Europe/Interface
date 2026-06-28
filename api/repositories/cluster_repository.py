"""Implémentation SQLAlchemy de `ClusterRepository`.

Lectures directes de la table `clusters` (~10k lignes, déjà indexée sur `cluster`,
`niveau_fragilite`, `citycode`) : aucune vue matérialisée nécessaire.
"""

from obrail_database.models import Cluster, Ville
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from repositories.interfaces import (
    ClusterGeoAggregate,
    ClusterProfilAggregate,
    ClusterSummaryAggregate,
    FragiliteMailleAggregate,
)

# liste blanche
_MAILLE_COLUMNS = {"code_dept": Ville.code_dept, "code_region": Ville.code_region}

# Liste blanche.
_PROFILE_COLUMNS = {
    "revenu_median_uc": Cluster.revenu_median_uc,
    "taux_sans_voiture": Cluster.taux_sans_voiture,
    "part_65plus": Cluster.part_65plus,
    "densite_pop_km2": Cluster.densite_pop_km2,
    "nb_trajets_total": Cluster.nb_trajets_total,
    "dist_gare_min_m": Cluster.dist_gare_min_m,
}

PROFILE_FEATURES = tuple(_PROFILE_COLUMNS)

# Libellés représentatifs d'un cluster : valeur la plus fréquente.
_NOM = func.mode().within_group(Cluster.cluster_nom.asc())
_NIVEAU = func.mode().within_group(Cluster.niveau_fragilite.asc())


def _as_float(value: object) -> float | None:
    return float(value) if value is not None else None


class SqlAlchemyClusterRepository:
    """Accès aux clusters de fragilité via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def clusters_carte(
        self, code_dept: str | None, code_region: str | None, has_gare: bool | None
    ) -> list[ClusterGeoAggregate]:
        stmt = select(
            Cluster.citycode,
            Cluster.city_name,
            Cluster.lat_insee,
            Cluster.lon_insee,
            Cluster.cluster,
            Cluster.cluster_nom,
            Cluster.niveau_fragilite,
        ).where(Cluster.lat_insee.isnot(None), Cluster.lon_insee.isnot(None))
        if has_gare is not None:
            stmt = stmt.where(Cluster.has_gare == has_gare)
        if code_dept or code_region:
            stmt = stmt.join(Ville, Ville.citycode == Cluster.citycode)
            if code_dept:
                stmt = stmt.where(Ville.code_dept == code_dept)
            if code_region:
                stmt = stmt.where(Ville.code_region == code_region)

        return [
            ClusterGeoAggregate(
                citycode=row.citycode,
                city_name=row.city_name,
                lat=row.lat_insee,
                lon=row.lon_insee,
                cluster=row.cluster,
                cluster_nom=row.cluster_nom,
                niveau_fragilite=row.niveau_fragilite,
            )
            for row in self._session.execute(stmt).all()
        ]

    def cluster_summaries(self) -> list[ClusterSummaryAggregate]:
        stmt = (
            select(
                Cluster.cluster,
                _NOM.label("cluster_nom"),
                _NIVEAU.label("niveau_fragilite"),
                func.count().label("effectif"),
            )
            .group_by(Cluster.cluster)
            .order_by(func.count().desc())
        )
        return [
            ClusterSummaryAggregate(
                cluster=row.cluster,
                cluster_nom=row.cluster_nom,
                niveau_fragilite=row.niveau_fragilite,
                effectif=row.effectif,
            )
            for row in self._session.execute(stmt).all()
        ]

    def cluster_profils(self, features: list[str]) -> list[ClusterProfilAggregate]:
        means = [func.avg(_PROFILE_COLUMNS[name]).label(name) for name in features]
        stmt = (
            select(
                Cluster.cluster,
                _NOM.label("cluster_nom"),
                _NIVEAU.label("niveau_fragilite"),
                func.count().label("effectif"),
                *means,
            )
            .group_by(Cluster.cluster)
            .order_by(Cluster.cluster)
        )
        return [
            ClusterProfilAggregate(
                cluster=row.cluster,
                cluster_nom=row.cluster_nom,
                niveau_fragilite=row.niveau_fragilite,
                effectif=row.effectif,
                feature_means={name: _as_float(getattr(row, name)) for name in features},
            )
            for row in self._session.execute(stmt).all()
        ]

    def fragilite_par_maille(self, by: str) -> list[FragiliteMailleAggregate]:
        maille = _MAILLE_COLUMNS[by]
        stmt = (
            select(maille.label("cle"), Cluster.niveau_fragilite, func.count().label("nb"))
            .join(Ville, Ville.citycode == Cluster.citycode)
            .where(maille.isnot(None), Cluster.niveau_fragilite.isnot(None))
            .group_by(maille, Cluster.niveau_fragilite)
        )
        repartitions: dict[str, dict[str, int]] = {}
        for row in self._session.execute(stmt).all():
            repartitions.setdefault(row.cle, {})[row.niveau_fragilite] = row.nb
        return [
            FragiliteMailleAggregate(cle=cle, repartition=rep)
            for cle, rep in sorted(repartitions.items())
        ]
