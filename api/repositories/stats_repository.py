"""Implémentation SQLAlchemy de `StatsRepository` (agrégations SQL)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import (
    DepartAggregate,
    JourNuitCounts,
    OperateurCount,
    OverviewAggregates,
)

# Agrégations calculées côté base (jamais de transfert de lignes brutes).
_OVERVIEW_SQL = text("""
SELECT
  count(*) AS total_trajets,
  count(*) FILTER (WHERE is_night_train) AS nb_nuit,
  count(DISTINCT agency_name) FILTER (WHERE agency_name IS NOT NULL AND agency_name <> '')
    AS nb_operateurs,
  (SELECT count(DISTINCT cc) FROM (
       SELECT departure_citycode AS cc FROM trajets WHERE departure_citycode IS NOT NULL
       UNION SELECT arrival_citycode FROM trajets WHERE arrival_citycode IS NOT NULL
   ) v) AS nb_villes_desservies,
  (SELECT count(DISTINCT pays) FROM (
       SELECT departure_country AS pays FROM trajets WHERE departure_country IS NOT NULL
         AND departure_country <> ''
       UNION SELECT arrival_country FROM trajets WHERE arrival_country IS NOT NULL
         AND arrival_country <> ''
   ) p) AS nb_pays,
  count(*) FILTER (
      WHERE departure_country IS NOT NULL AND arrival_country IS NOT NULL
        AND departure_country <> arrival_country
  ) AS nb_transfrontalier,
  percentile_cont(0.5) WITHIN GROUP (ORDER BY distance_km) AS distance_mediane_km,
  avg(co2_per_pkm) AS co2_moyen_par_pkm,
  coalesce(sum(emissions_co2), 0) AS emissions_co2_totales_g
FROM trajets
""")

_JOUR_NUIT_SQL = text("""
SELECT
  count(*) FILTER (WHERE is_night_train IS NOT TRUE) AS nb_jour,
  count(*) FILTER (WHERE is_night_train) AS nb_nuit
FROM trajets
""")

_OPERATEURS_SQL = text("""
SELECT agency_name,
       count(*) AS nb_trajets,
       count(*) FILTER (WHERE is_night_train) AS nb_nuit
FROM trajets
WHERE agency_name IS NOT NULL AND agency_name <> ''
GROUP BY agency_name
ORDER BY nb_trajets DESC
LIMIT :limit
""")

# jointure trajets → villes par citycode résolu.
_DEPARTS_SQL = text("""
SELECT v.citycode, v.city_name, v.lat_insee AS lat, v.lon_insee AS lon, count(*) AS nb_trajets
FROM trajets t
JOIN villes v ON v.citycode = t.departure_citycode
WHERE v.lat_insee IS NOT NULL AND v.lon_insee IS NOT NULL
GROUP BY v.citycode, v.city_name, v.lat_insee, v.lon_insee
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
