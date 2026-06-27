"""Implémentation SQLAlchemy de `TerritoireRepository`.

Lectures directes de la table `villes` (~10k lignes) : aucune vue matérialisée
n'est nécessaire (agrégations triviales), et les colonnes filtrées sont déjà
indexées au schéma (`code_dept`, `code_region`, `has_gare`).
"""

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from models import Ville
from repositories.interfaces import (
    AmplitudeAggregate,
    AmplitudeBinAggregate,
    CouvertureMailleAggregate,
    VilleGeoAggregate,
)

# Liste blanche des dimensions cartographiables (nom public -> colonne ORM).
_DIMENSIONS = {
    "nb_trajets_total": Ville.nb_trajets_total,
    "has_gare": Ville.has_gare,
    "accessibilite_ord": Ville.accessibilite_ord,
    "dist_gare_min_m": Ville.dist_gare_min_m,
}

DIMENSIONS = tuple(_DIMENSIONS)

# Liste blanche des mailles d'agrégation.
_MAILLES = {
    "code_dept": Ville.code_dept,
    "code_region": Ville.code_region,
}

MAILLES = tuple(_MAILLES)


def _as_float(value: object) -> float | None:
    return float(value) if value is not None else None


class SqlAlchemyTerritoireRepository:
    """Accès aux données territoriales via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def villes_carte(
        self,
        dimension: str,
        code_dept: str | None,
        code_region: str | None,
        has_gare: bool | None,
    ) -> list[VilleGeoAggregate]:
        col = _DIMENSIONS[dimension]
        stmt = select(
            Ville.citycode,
            Ville.city_name,
            Ville.lat_insee,
            Ville.lon_insee,
            Ville.population_insee,
            Ville.has_gare,
            col.label("valeur"),
        ).where(Ville.lat_insee.isnot(None), Ville.lon_insee.isnot(None))
        if code_dept:
            stmt = stmt.where(Ville.code_dept == code_dept)
        if code_region:
            stmt = stmt.where(Ville.code_region == code_region)
        if has_gare is not None:
            stmt = stmt.where(Ville.has_gare == has_gare)

        rows = self._session.execute(stmt).all()
        return [
            VilleGeoAggregate(
                citycode=row.citycode,
                city_name=row.city_name,
                lat=row.lat_insee,
                lon=row.lon_insee,
                population=_as_float(row.population_insee),
                valeur=_as_float(row.valeur),
                has_gare=row.has_gare,
            )
            for row in rows
        ]

    def couverture(self, by: str) -> list[CouvertureMailleAggregate]:
        col = _MAILLES[by]
        stmt = (
            select(
                col.label("cle"),
                func.count().label("nb_communes"),
                func.avg(cast(Ville.has_gare, Integer)).label("taux_avec_gare"),
                func.coalesce(func.sum(Ville.nb_trajets_total), 0).label("nb_trajets_total"),
                func.avg(Ville.accessibilite_ord).label("accessibilite_moy"),
            )
            .where(col.isnot(None))
            .group_by(col)
            .order_by(func.coalesce(func.sum(Ville.nb_trajets_total), 0).desc())
        )
        rows = self._session.execute(stmt).all()
        return [
            CouvertureMailleAggregate(
                cle=row.cle,
                nb_communes=row.nb_communes,
                taux_avec_gare=float(row.taux_avec_gare or 0.0),
                nb_trajets_total=int(row.nb_trajets_total),
                accessibilite_moy=_as_float(row.accessibilite_moy),
            )
            for row in rows
        ]

    def amplitude(self, bin_h: float) -> AmplitudeAggregate:
        bucket = func.floor(Ville.amplitude_moy_h / bin_h) * bin_h
        bins_stmt = (
            select(bucket.label("min_h"), func.count().label("nb_communes"))
            .where(Ville.amplitude_moy_h.isnot(None))
            .group_by(bucket)
            .order_by(bucket)
        )
        bins = [
            AmplitudeBinAggregate(
                min_h=float(row.min_h),
                max_h=float(row.min_h) + bin_h,
                nb_communes=row.nb_communes,
            )
            for row in self._session.execute(bins_stmt).all()
        ]
        part = self._session.scalar(
            select(func.avg(cast(Ville.dernier_depart_apres_minuit, Integer))).where(
                Ville.dernier_depart_apres_minuit.isnot(None)
            )
        )
        return AmplitudeAggregate(bins=bins, part_apres_minuit=float(part or 0.0))
