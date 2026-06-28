"""Vues matérialisées des agrégats du dashboard.

Les endpoints d'agrégation portent sur l'ensemble des trajets (~13M lignes) : un index
classique n'accélère pas une agrégation plein-table. On **précalcule** donc ces agrégats
dans des vues matérialisées, rafraîchies après chaque chargement ETL.

Chaque vue a un **index unique** : il garantit l'unicité de la clé et permet le
`REFRESH MATERIALIZED VIEW CONCURRENTLY` (rafraîchissement sans bloquer les lectures).

Registre unique (réutilisé par les migrations Alembic, l'ETL et les tests). Chaque
migration ne gère que les vues de son onglet (groupes `OVERVIEW_VIEWS`, `EXPLORER_VIEWS`,
`CARBON_VIEWS`, `QUALITE_VIEWS`).
"""

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from obrail_database.models import Cluster, Trajet, Ville

# Tables auditées par l'onglet « Qualité des données » (nom public -> modèle ORM).
_QUALITE_TABLES = {"trajets": Trajet, "villes": Ville, "clusters": Cluster}


def _completude_block(table_name: str, model: type) -> str:
    """Bloc SQL comptant les NULLs de chaque colonne d'une table (un seul scan).

    Compte tous les NULLs en une passe, puis dé-pivote en lignes (colonne, nb_nuls)
    via `VALUES` - bien plus efficace qu'un scan par colonne sur ~13M trajets.
    """
    cols = [c.name for c in model.__table__.columns]
    null_counts = ", ".join(f"count(*) FILTER (WHERE {c} IS NULL) AS n_{c}" for c in cols)
    values = ", ".join(f"('{c}', t.n_{c})" for c in cols)
    return (
        f"SELECT '{table_name}' AS source_table, v.colonne, v.nb_nuls, t.nb_lignes "
        f"FROM (SELECT count(*) AS nb_lignes, {null_counts} FROM {table_name}) t "
        f"CROSS JOIN LATERAL (VALUES {values}) AS v(colonne, nb_nuls)"
    )


def _completude_view_sql() -> str:
    """Génère la vue de complétude (NULLs par colonne) pour les 3 tables."""
    blocks = " UNION ALL ".join(
        _completude_block(name, model) for name, model in _QUALITE_TABLES.items()
    )
    return f"CREATE MATERIALIZED VIEW IF NOT EXISTS mv_qualite_completude AS {blocks}"


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
    "mv_distance_hist": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_distance_hist AS
        SELECT
          floor(distance_km / 25) * 25 AS bin_min,  -- bins de 25 km
          count(*) FILTER (WHERE is_night_train IS NOT TRUE) AS count_jour,
          count(*) FILTER (WHERE is_night_train) AS count_nuit
        FROM trajets
        WHERE mode = 'train' AND distance_km IS NOT NULL
        GROUP BY floor(distance_km / 25)
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_distance_hist_bin ON mv_distance_hist (bin_min)",
    ),
    "mv_co2_comparaison": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_co2_comparaison AS
        SELECT
          floor(distance_km / 50) * 50 AS dist_min,      -- tranches de 50 km
          count(*) AS nb_trajets,
          sum(distance_km) AS train_pkm,                 -- voyageur-km (1 voyageur / trajet)
          sum(emissions_co2) AS train_emissions_g
        FROM trajets
        WHERE mode = 'train' AND distance_km IS NOT NULL AND emissions_co2 IS NOT NULL
        GROUP BY floor(distance_km / 50)
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_co2_comparaison_bin "
        "ON mv_co2_comparaison (dist_min)",
    ),
    "mv_carbon_density": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_carbon_density AS
        SELECT
          mode,
          floor(distance_km / 50) * 50 + 25 AS dist_mid,  -- centre du bin (50 km)
          floor(co2_per_pkm / 2) * 2 + 1 AS co2_mid,       -- centre du bin (2 g/pkm)
          count(*) AS nb_trajets
        FROM trajets
        WHERE mode IN ('train', 'flight')
          AND distance_km IS NOT NULL AND co2_per_pkm IS NOT NULL
        GROUP BY mode, floor(distance_km / 50), floor(co2_per_pkm / 2)
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_carbon_density_cell "
        "ON mv_carbon_density (mode, dist_mid, co2_mid)",
    ),
    "mv_co2_distribution": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_co2_distribution AS
        SELECT
          mode,
          count(*) AS nb_trajets,
          min(co2_per_pkm) AS co2_min,
          percentile_cont(0.25) WITHIN GROUP (ORDER BY co2_per_pkm) AS co2_q1,
          percentile_cont(0.50) WITHIN GROUP (ORDER BY co2_per_pkm) AS co2_median,
          percentile_cont(0.75) WITHIN GROUP (ORDER BY co2_per_pkm) AS co2_q3,
          max(co2_per_pkm) AS co2_max,
          avg(co2_per_pkm) AS co2_moy
        FROM trajets
        WHERE mode IN ('train', 'flight') AND co2_per_pkm IS NOT NULL
        GROUP BY mode
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_co2_distribution_mode "
        "ON mv_co2_distribution (mode)",
    ),
    # Onglet « Qualité des données » : audits plein-table sur ~13M trajets → précalcul.
    "mv_qualite_completude": (
        _completude_view_sql(),
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_qualite_completude_col "
        "ON mv_qualite_completude (source_table, colonne)",
    ),
    "mv_qualite_anomalies": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_qualite_anomalies AS
        SELECT * FROM (VALUES
          ('trip_id_dupliques', 'trip_id partagés par plusieurs trajets',
            (SELECT count(*) FROM (SELECT trip_id FROM trajets WHERE trip_id IS NOT NULL
                GROUP BY trip_id HAVING count(*) > 1) d), 'warn'),
          ('depart_non_resolu', 'Trajets sans commune de départ résolue',
            (SELECT count(*) FROM trajets WHERE departure_citycode IS NULL), 'warn'),
          ('arrivee_non_resolue', 'Trajets sans commune d''arrivée résolue',
            (SELECT count(*) FROM trajets WHERE arrival_citycode IS NULL), 'warn'),
          ('distance_manquante', 'Trajets sans distance renseignée',
            (SELECT count(*) FROM trajets WHERE distance_km IS NULL), 'info'),
          ('cluster_non_rattache', 'Communes (clusters) non rattachées à une ville',
            (SELECT count(*) FROM clusters WHERE citycode IS NULL), 'info'),
          ('ville_sans_coordonnees', 'Villes sans coordonnées géographiques',
            (SELECT count(*) FROM villes WHERE lat_insee IS NULL OR lon_insee IS NULL), 'error')
        ) AS a(type, libelle, nb, severite)
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_qualite_anomalies_type "
        "ON mv_qualite_anomalies (type)",
    ),
    "mv_qualite_volumetrie": (
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_qualite_volumetrie AS
        SELECT coalesce(source, '(inconnu)') AS cle, count(*) AS nb
        FROM trajets
        GROUP BY coalesce(source, '(inconnu)')
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_qualite_volumetrie_cle "
        "ON mv_qualite_volumetrie (cle)",
    ),
}

OVERVIEW_VIEWS = ("mv_overview_kpi", "mv_operateurs", "mv_departs")
EXPLORER_VIEWS = ("mv_liaisons", "mv_distance_hist")
CARBON_VIEWS = ("mv_co2_comparaison", "mv_carbon_density", "mv_co2_distribution")
QUALITE_VIEWS = ("mv_qualite_completude", "mv_qualite_anomalies", "mv_qualite_volumetrie")
ALL_VIEWS = OVERVIEW_VIEWS + EXPLORER_VIEWS + CARBON_VIEWS + QUALITE_VIEWS


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
