"""Fabrique de moteur SQLAlchemy pour l'ETL, les migrations et les tests."""

from sqlalchemy import Engine, create_engine

from obrail_database.config import settings


def create_db_engine(url: str | None = None) -> Engine:
    """Crée un moteur SQLAlchemy (paresseux : aucune connexion à l'import)."""
    return create_engine(url or settings.database_url, pool_pre_ping=True, future=True)
