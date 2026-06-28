"""Chargement des sources CSV dans PostgreSQL.

- `villes` / `clusters` (~10k lignes) : lecture CSV + cast typé + insert en masse.
- `trajets` (~13M lignes) : `COPY` PostgreSQL (chemin rapide), en s'appuyant sur le
  parsing natif des dates `YYYYMMDD` et des booléens `True`/`False`.
"""

import csv
from pathlib import Path

from sqlalchemy import insert, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from obrail_database.etl.transform import row_to_mapping
from obrail_database.models import Cluster, Trajet, Ville


def _load_csv_orm(session: Session, model: type, csv_path: Path) -> int:
    with open(csv_path, encoding="utf-8") as f:
        rows = [row_to_mapping(r, model) for r in csv.DictReader(f)]
    if rows:
        session.execute(insert(model), rows)
    return len(rows)


def load_villes(session: Session, csv_path: Path) -> int:
    """Charge `villes_enriched.csv` dans la table `villes`."""
    return _load_csv_orm(session, Ville, csv_path)


def load_clusters(session: Session, csv_path: Path) -> int:
    """Charge `clusters_final.csv` dans la table `clusters`."""
    return _load_csv_orm(session, Cluster, csv_path)


def load_trajets(engine: Engine, csv_path: Path, limit: int | None = None) -> None:
    """Charge `routes_france.csv` dans `trajets` via `COPY` (limit = nb de lignes max)."""
    with open(csv_path, encoding="utf-8") as f:
        header = f.readline().strip()
    cols = [c.strip() for c in header.split(",")]
    unknown = [c for c in cols if c not in Trajet.__table__.columns]
    if unknown:
        raise ValueError(f"Colonnes inconnues dans {csv_path.name} : {unknown}")

    copy_sql = f"COPY trajets ({', '.join(cols)}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    raw = engine.raw_connection()
    try:
        dbapi = raw.driver_connection
        with dbapi.cursor() as cur, cur.copy(copy_sql) as copy, open(csv_path, "rb") as fb:
            if limit is None:
                while chunk := fb.read(1 << 20):
                    copy.write(chunk)
            else:
                for i, line in enumerate(fb):  # i == 0 : ligne d'en-tête
                    copy.write(line)
                    if i >= limit:
                        break
        dbapi.commit()
    finally:
        raw.close()


def truncate_all(session: Session) -> None:
    """Vide les 3 tables (réinitialise les identités) avant un rechargement complet."""
    session.execute(text("TRUNCATE villes, clusters, trajets RESTART IDENTITY CASCADE"))
