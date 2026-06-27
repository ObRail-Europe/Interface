"""Vues matérialisées des agrégats du dashboard.

Les endpoints d'agrégation portent sur l'ensemble des trajets (~13M lignes) : un index
classique n'accélère pas une agrégation plein-table. On **précalcule** donc ces agrégats
dans des vues matérialisées, rafraîchies après chaque chargement ETL.

Chaque vue a un **index unique** : il garantit l'unicité de la clé et permet le
`REFRESH MATERIALIZED VIEW CONCURRENTLY` (rafraîchissement sans bloquer les lectures).

Registre unique (réutilisé par les migrations Alembic, l'ETL et les tests). Chaque
migration ne gère que les vues de son onglet (groupes `OVERVIEW_VIEWS`, `EXPLORER_VIEWS`).
"""

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

# nom de vue -> (SQL de création de la vue, SQL de l'index unique)
_VIEW_DDL: dict[str, tuple[str, str]] = {
    "mv_overview_kpi": (
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
    ),
    "mv_operateurs": (
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
    ),
    "mv_departs": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_departs AS
        SELECT v.citycode, v.city_name, v.lat_insee AS lat, v.lon_insee AS lon,
               count(*) AS nb_trajets
        FROM trajets t
        JOIN villes v ON v.citycode = t.departure_citycode
        WHERE v.lat_insee IS NOT NULL AND v.lon_insee IS NOT NULL
        GROUP BY v.citycode, v.city_name, v.lat_insee, v.lon_insee
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_departs_citycode ON mv_departs (citycode)",
    ),
    "mv_liaisons": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_liaisons AS
        SELECT
          dv.citycode AS dep_citycode, dv.city_name AS dep_city,
          dv.lat_insee AS dep_lat, dv.lon_insee AS dep_lon,
          av.citycode AS arr_citycode, av.city_name AS arr_city,
          av.lat_insee AS arr_lat, av.lon_insee AS arr_lon,
          count(*) AS nb_trajets,
          count(*) FILTER (WHERE t.is_night_train) AS nb_nuit,
          avg(t.distance_km) AS distance_moy_km,
          avg(t.co2_per_pkm) AS co2_moy_par_pkm
        FROM trajets t
        JOIN villes dv ON dv.citycode = t.departure_citycode
        JOIN villes av ON av.citycode = t.arrival_citycode
        WHERE t.mode = 'train'  -- exclut les vols
          AND dv.citycode <> av.citycode  -- exclus les boucles
          AND dv.lat_insee IS NOT NULL AND dv.lon_insee IS NOT NULL
          AND av.lat_insee IS NOT NULL AND av.lon_insee IS NOT NULL
        GROUP BY dv.citycode, dv.city_name, dv.lat_insee, dv.lon_insee,
                 av.citycode, av.city_name, av.lat_insee, av.lon_insee
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_liaisons_od "
        "ON mv_liaisons (dep_citycode, arr_citycode)",
    ),
}

# Groupes par onglet (chaque migration ne gère que son groupe).
OVERVIEW_VIEWS = ("mv_overview_kpi", "mv_operateurs", "mv_departs")
EXPLORER_VIEWS = ("mv_liaisons",)
ALL_VIEWS = OVERVIEW_VIEWS + EXPLORER_VIEWS


def create_views(connection: Connection, names: Iterable[str]) -> None:
    """Crée les vues matérialisées indiquées et leurs index (idempotent)."""
    for name in names:
        for statement in _VIEW_DDL[name]:
            connection.execute(text(statement))


def drop_views(connection: Connection, names: Iterable[str]) -> None:
    """Supprime les vues matérialisées indiquées."""
    for name in names:
        connection.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {name}"))


def refresh_views(engine: Engine, names: Iterable[str] = ALL_VIEWS) -> None:
    """Rafraîchit les vues (hors transaction : CONCURRENTLY l'exige)."""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        for name in names:
            connection.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {name}"))
