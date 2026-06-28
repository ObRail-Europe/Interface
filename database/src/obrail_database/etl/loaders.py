"""Chargement des sources CSV dans PostgreSQL.

- `villes` / `clusters` (~10k lignes) : lecture CSV + cast typé + insert en masse.
- `trajets` (~13M lignes) : `COPY` PostgreSQL (chemin rapide), en s'appuyant sur le
  parsing natif des dates `YYYYMMDD` et des booléens `True`/`False`.
"""

import csv
from pathlib import Path

from sqlalchemy import func, insert, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
import polars as pl

from obrail_database.etl.transform import row_to_mapping, prepare_trajet_types
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


def load_trajets(engine: Engine, parquet_path: Path, limit: int | None = None) -> None:
    """Charge `routes_france.parquet` dans `trajets` via `COPY` (limit = nb de lignes max)."""
    schema = pl.read_parquet_schema(parquet_path)
    cols = list(schema.keys())

    unknown = [c for c in cols if c not in Trajet.__table__.columns]
    if unknown:
        raise ValueError(f"Colonnes inconnues dans {parquet_path.name} : {unknown}")

    if limit:
        df = pl.scan_parquet(parquet_path).head(limit).collect()
    else:
        df = pl.read_parquet(parquet_path)

    df = prepare_trajet_types(df)
    
    connection_uri = engine.url.render_as_string(hide_password=False)
    connection_uri = connection_uri.replace("postgresql+psycopg://", "postgresql://")

    df.write_database(
        table_name="trajets",
        connection=connection_uri,
        if_table_exists="append",
        engine="adbc"
    )


def truncate_all(session: Session) -> None:
    """Vide les 3 tables (réinitialise les identités) avant un rechargement complet."""
    session.execute(text("TRUNCATE villes, clusters, trajets RESTART IDENTITY CASCADE"))


def is_database_empty(session: Session) -> bool:
    """Vérifie si la base est vide (aucune ligne dans les 3 tables)."""
    for model in (Ville, Cluster, Trajet):
        count = session.scalar(select(func.count()).select_from(model))
        if count:
            return False
    return True
