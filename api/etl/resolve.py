"""Résolution des clés de jointure inter-sources (point 4).

- `clusters.citycode` : correspondance **par coordonnées** avec `villes` (100 %,
  insensible aux homonymes).
- `trajets.departure/arrival_citycode` : correspondance **par nom normalisé**
  (`lower(unaccent(...))`), homonymes tranchés par `has_gare` puis `population`,
  alias de préfixe pour les grandes villes subdivisées (Paris/Lyon/Marseille).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

# Communes subdivisées en trajets (« Paris 16 Passy » → commune « Paris »).
_ALIAS_BASES = ("paris", "lyon", "marseille")


def resolve_clusters(session: Session) -> int:
    """Renseigne `clusters.citycode` par correspondance de coordonnées avec `villes`."""
    result = session.execute(
        text(
            """
            UPDATE clusters c
            SET citycode = v.citycode
            FROM villes v
            WHERE round(c.lat_insee::numeric, 4) = round(v.lat_insee::numeric, 4)
              AND round(c.lon_insee::numeric, 4) = round(v.lon_insee::numeric, 4)
            """
        )
    )
    return result.rowcount


def resolve_trajets(session: Session) -> None:
    """Renseigne `trajets.departure/arrival_citycode` par nom normalisé + alias."""
    session.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))

    # Table de correspondance nom_normalisé → citycode, homonymes tranchés.
    session.execute(text("DROP TABLE IF EXISTS ville_lookup"))
    session.execute(
        text(
            """
            CREATE TEMP TABLE ville_lookup AS
            SELECT DISTINCT ON (lower(unaccent(city_name)))
                   lower(unaccent(city_name)) AS name_norm, citycode
            FROM villes
            ORDER BY lower(unaccent(city_name)),
                     has_gare DESC NULLS LAST, population_insee DESC NULLS LAST
            """
        )
    )
    session.execute(text("CREATE INDEX ix_ville_lookup_norm ON ville_lookup(name_norm)"))

    for side in ("departure", "arrival"):
        # 1) correspondance exacte par nom normalisé (côté FR).
        session.execute(
            text(
                f"""
                UPDATE trajets t
                SET {side}_citycode = vl.citycode
                FROM ville_lookup vl
                WHERE t.{side}_country = 'FR'
                  AND lower(unaccent(t.{side}_city)) = vl.name_norm
                """
            )
        )
        # 2) alias de préfixe pour les grandes villes subdivisées.
        session.execute(
            text(
                f"""
                UPDATE trajets t
                SET {side}_citycode = base.citycode
                FROM (
                    SELECT lower(unaccent(city_name)) AS base_name, citycode
                    FROM villes
                    WHERE lower(unaccent(city_name)) = ANY(:bases)
                ) base
                WHERE t.{side}_citycode IS NULL
                  AND t.{side}_country = 'FR'
                  AND split_part(lower(unaccent(t.{side}_city)), ' ', 1) = base.base_name
                """
            ),
            {"bases": list(_ALIAS_BASES)},
        )


_STATS_SQL = text("""
SELECT
  (SELECT count(*) FROM clusters) AS clusters_total,
  (SELECT count(*) FROM clusters WHERE citycode IS NOT NULL) AS clusters_resolus,
  (SELECT count(*) FROM trajets) AS trajets_total,
  (SELECT count(*) FROM trajets WHERE departure_citycode IS NOT NULL) AS depart_resolus,
  (SELECT count(*) FROM trajets WHERE arrival_citycode IS NOT NULL) AS arrivee_resolus
""")


def resolution_stats(session: Session) -> dict[str, int]:
    """Compteurs de résolution (pour le suivi qualité)."""
    return dict(session.execute(_STATS_SQL).mappings().one())
