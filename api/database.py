"""Accès base de données : moteur SQLAlchemy et dépendance de session FastAPI.

`create_engine` est paresseux (aucune connexion n'est ouverte à l'import), ce qui
permet d'importer ce module sans Postgres démarré.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session]:
    """Fournit une session SQLAlchemy par requête et la ferme."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
