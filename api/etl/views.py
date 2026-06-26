"""Vues matérialisées de l'onglet « Vue d'ensemble ».

Les agrégats des endpoints stats portent sur l'ensemble des trajets (~13M lignes) :
un index classique n'accélère pas une agrégation plein-table. On **précalcule** donc
ces agrégats dans des vues matérialisées, rafraîchies après chaque chargement ETL.

Chaque vue a un **index unique** : il garantit l'unicité de la clé et permet le
`REFRESH MATERIALIZED VIEW CONCURRENTLY` (rafraîchissement sans bloquer les lectures).

Défini ici (et non en ORM, qui ne gère pas les vues matérialisées) et réutilisé par la
migration Alembic, l'ETL (`etl.run`) et les tests — une seule source de vérité.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

_CREATE_STATEMENTS = (
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_overview_kpi AS
    SELECT
      1 AS id,
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
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_overview_kpi_id ON mv_overview_kpi (id)",
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_operateurs AS
    SELECT agency_name,
           count(*) AS nb_trajets,
           count(*) FILTER (WHERE is_night_train) AS nb_nuit
    FROM trajets
    WHERE agency_name IS NOT NULL AND agency_name <> ''
    GROUP BY agency_name
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_operateurs_agency ON mv_operateurs (agency_name)",
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_departs AS
    SELECT v.citycode, v.city_name, v.lat_insee AS lat, v.lon_insee AS lon, count(*) AS nb_trajets
    FROM trajets t
    JOIN villes v ON v.citycode = t.departure_citycode
    WHERE v.lat_insee IS NOT NULL AND v.lon_insee IS NOT NULL
    GROUP BY v.citycode, v.city_name, v.lat_insee, v.lon_insee
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_departs_citycode ON mv_departs (citycode)",
)

_DROP_STATEMENTS = (
    "DROP MATERIALIZED VIEW IF EXISTS mv_overview_kpi",
    "DROP MATERIALIZED VIEW IF EXISTS mv_operateurs",
    "DROP MATERIALIZED VIEW IF EXISTS mv_departs",
)

# CONCURRENTLY : ne bloque pas les lectures du dashboard pendant le rafraîchissement
# (nécessite l'index unique et une vue déjà peuplée).
_REFRESH_STATEMENTS = (
    "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_overview_kpi",
    "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_operateurs",
    "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_departs",
)


def create_views(connection: Connection) -> None:
    """Crée les vues matérialisées et leurs index (idempotent)."""
    for statement in _CREATE_STATEMENTS:
        connection.execute(text(statement))


def drop_views(connection: Connection) -> None:
    """Supprime les vues matérialisées."""
    for statement in _DROP_STATEMENTS:
        connection.execute(text(statement))


def refresh_views(engine: Engine) -> None:
    """Rafraîchit les vues (hors transaction : CONCURRENTLY l'exige)."""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        for statement in _REFRESH_STATEMENTS:
            connection.execute(text(statement))
