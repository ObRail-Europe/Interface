"""Ingestion ETL ObRail : charge les CSV de `data/` dans PostgreSQL.

Exemples :
  uv run python -m etl.run                      # ingestion complète
  uv run python -m etl.run --trajets-limit 100000
  uv run python -m etl.run --skip-trajets
"""

import argparse
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from obrail_database.config import settings
from obrail_database.engine import create_db_engine
from obrail_database.etl.loaders import (
    is_database_empty,
    load_clusters,
    load_trajets,
    load_villes,
    truncate_all,
)
from obrail_database.etl.resolve import resolution_stats, resolve_clusters, resolve_trajets
from obrail_database.etl.views import refresh_views
from obrail_database.logging_config import configure_logging
from obrail_database.models import Trajet

logger = logging.getLogger("obrail.etl")

# data/ à la racine du dépôt (ou /data dans le conteneur).
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[4] / "data"


def main() -> None:
    configure_logging(settings.log_level)
    engine = create_db_engine()
    parser = argparse.ArgumentParser(description="Ingestion ETL ObRail")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--trajets-limit", type=int, default=None, help="nb max de trajets")
    parser.add_argument("--skip-trajets", action="store_true")
    parser.add_argument("--skip-resolve", action="store_true", help="ne pas résoudre les jointures")
    parser.add_argument("--no-truncate", action="store_true")
    parser.add_argument(
        "--force", action="store_true", help="force l'ingestion même si la base n'est pas vide"
    )
    args = parser.parse_args()

    logger.info("ETL start (data_dir=%s)", args.data_dir)
    with Session(engine) as session:
        if not is_database_empty(session) and not args.force:
            logger.info("Database is not empty. Use --force to overwrite.")
            return

        if not args.no_truncate:
            truncate_all(session)
            session.commit()
        n_villes = load_villes(session, args.data_dir / "villes_enriched.csv")
        session.commit()
        logger.info("villes loaded: %d rows", n_villes)
        n_clusters = load_clusters(session, args.data_dir / "clusters_final.csv")
        session.commit()
        logger.info("clusters loaded: %d rows", n_clusters)

    if args.skip_trajets:
        logger.info("trajets skipped (--skip-trajets)")
    else:
        load_trajets(engine, args.data_dir / "routes_france.csv", limit=args.trajets_limit)
        with Session(engine) as session:
            n_trajets = session.scalar(select(func.count()).select_from(Trajet))
        logger.info("trajets loaded: %s rows", n_trajets)

    if not args.skip_resolve:
        with Session(engine) as session:
            n_clusters = resolve_clusters(session)
            if not args.skip_trajets:
                resolve_trajets(session)
            session.commit()
            stats = resolution_stats(session)
        logger.info("resolved clusters.citycode: %d/%d", n_clusters, stats["clusters_total"])
        if not args.skip_trajets:
            total = stats["trajets_total"] or 1
            logger.info(
                "resolved trajets: départ %d/%d (%.0f%%), arrivée %d/%d (%.0f%%)",
                stats["depart_resolus"],
                total,
                100 * stats["depart_resolus"] / total,
                stats["arrivee_resolus"],
                total,
                100 * stats["arrivee_resolus"] / total,
            )

    refresh_views(engine)  # met à jour les vues matérialisées
    logger.info("materialized views refreshed")
    logger.info("ETL done")


if __name__ == "__main__":
    main()
