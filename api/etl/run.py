"""Ingestion ETL ObRail : charge les CSV de `data/` dans PostgreSQL.

Exemples :
  uv run python -m etl.run                      # ingestion complète
  uv run python -m etl.run --trajets-limit 100000
  uv run python -m etl.run --skip-trajets
"""

import argparse
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import engine
from etl.loaders import load_clusters, load_trajets, load_villes, truncate_all
from etl.resolve import resolution_stats, resolve_clusters, resolve_trajets
from etl.views import refresh_views
from models import Trajet

# data/ à la racine du dépôt (ou /data dans le conteneur).
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion ETL ObRail")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--trajets-limit", type=int, default=None, help="nb max de trajets")
    parser.add_argument("--skip-trajets", action="store_true")
    parser.add_argument("--skip-resolve", action="store_true", help="ne pas résoudre les jointures")
    parser.add_argument("--no-truncate", action="store_true")
    args = parser.parse_args()

    with Session(engine) as session:
        if not args.no_truncate:
            truncate_all(session)
            session.commit()
        n_villes = load_villes(session, args.data_dir / "villes_enriched.csv")
        session.commit()
        print(f"villes   : {n_villes} lignes")
        n_clusters = load_clusters(session, args.data_dir / "clusters_final.csv")
        session.commit()
        print(f"clusters : {n_clusters} lignes")

    if args.skip_trajets:
        print("trajets  : ignoré (--skip-trajets)")
    else:
        load_trajets(engine, args.data_dir / "routes_france.csv", limit=args.trajets_limit)
        with Session(engine) as session:
            n_trajets = session.scalar(select(func.count()).select_from(Trajet))
        print(f"trajets  : {n_trajets} lignes")

    if not args.skip_resolve:
        with Session(engine) as session:
            n_clusters = resolve_clusters(session)
            if not args.skip_trajets:
                resolve_trajets(session)
            session.commit()
            stats = resolution_stats(session)
        print(f"résolu   : clusters.citycode {n_clusters}/{stats['clusters_total']}")
        if not args.skip_trajets:
            total = stats["trajets_total"] or 1
            print(
                f"           trajets départ {stats['depart_resolus']}/{total} "
                f"({100 * stats['depart_resolus'] / total:.0f}%), "
                f"arrivée {stats['arrivee_resolus']}/{total} "
                f"({100 * stats['arrivee_resolus'] / total:.0f}%)"
            )

    refresh_views(engine)  # met à jour les vues matérialisées de la vue d'ensemble
    print("vues     : rafraîchies")


if __name__ == "__main__":
    main()
