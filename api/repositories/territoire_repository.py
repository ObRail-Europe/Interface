"""Implémentation SQLAlchemy de `TerritoireRepository`.

Lectures directes de la table `villes` (~10k lignes) : aucune vue matérialisée
n'est nécessaire (agrégations triviales), et les colonnes filtrées sont déjà
indexées au schéma (`code_dept`, `code_region`, `has_gare`).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Ville
from repositories.interfaces import VilleGeoAggregate

# Liste blanche des dimensions cartographiables (nom public -> colonne ORM).
_DIMENSIONS = {
    "nb_trajets_total": Ville.nb_trajets_total,
    "has_gare": Ville.has_gare,
    "accessibilite_ord": Ville.accessibilite_ord,
    "dist_gare_min_m": Ville.dist_gare_min_m,
}

DIMENSIONS = tuple(_DIMENSIONS)


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
