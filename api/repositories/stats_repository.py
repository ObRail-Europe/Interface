"""Implémentation SQLAlchemy de `StatsRepository` (agrégations SQL)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import (
    DepartAggregate,
    JourNuitCounts,
    OperateurCount,
    OverviewAggregates,
)

# Lecture des vues matérialisées (agrégats précalculés, cf. etl/views.py).
_OVERVIEW_SQL = text("""
SELECT total_trajets, nb_nuit, nb_operateurs, nb_villes_desservies, nb_pays,
       nb_transfrontalier, distance_mediane_km, co2_moyen_par_pkm, emissions_co2_totales_g
FROM mv_overview_kpi
""")

_JOUR_NUIT_SQL = text("""
SELECT total_trajets - nb_nuit AS nb_jour, nb_nuit
FROM mv_overview_kpi
""")

_OPERATEURS_SQL = text("""
SELECT agency_name, nb_trajets, nb_nuit
FROM mv_operateurs
ORDER BY nb_trajets DESC
LIMIT :limit
""")

_DEPARTS_SQL = text("""
SELECT citycode, city_name, lat, lon, nb_trajets
FROM mv_departs
ORDER BY nb_trajets DESC
""")


class SqlAlchemyStatsRepository:
    """Accès aux statistiques via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def overview_aggregates(self) -> OverviewAggregates:
        row = self._session.execute(_OVERVIEW_SQL).mappings().one()
        return OverviewAggregates(
            total_trajets=row["total_trajets"],
            nb_nuit=row["nb_nuit"],
            nb_operateurs=row["nb_operateurs"],
            nb_villes_desservies=row["nb_villes_desservies"],
            nb_pays=row["nb_pays"],
            nb_transfrontalier=row["nb_transfrontalier"],
            distance_mediane_km=row["distance_mediane_km"],
            co2_moyen_par_pkm=row["co2_moyen_par_pkm"],
            emissions_co2_totales_g=float(row["emissions_co2_totales_g"]),
        )

    def jour_nuit_counts(self) -> JourNuitCounts:
        row = self._session.execute(_JOUR_NUIT_SQL).mappings().one()
        return JourNuitCounts(nb_jour=row["nb_jour"], nb_nuit=row["nb_nuit"])

    def top_operateurs(self, limit: int) -> list[OperateurCount]:
        rows = self._session.execute(_OPERATEURS_SQL, {"limit": limit}).mappings().all()
        return [
            OperateurCount(
                agency_name=row["agency_name"],
                nb_trajets=row["nb_trajets"],
                nb_nuit=row["nb_nuit"],
            )
            for row in rows
        ]

    def departs(self) -> list[DepartAggregate]:
        rows = self._session.execute(_DEPARTS_SQL).mappings().all()
        return [
            DepartAggregate(
                citycode=row["citycode"],
                city_name=row["city_name"],
                lat=row["lat"],
                lon=row["lon"],
                nb_trajets=row["nb_trajets"],
            )
            for row in rows
        ]
