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


def init_db() -> None:
    """Crée toutes les tables ORM dans la base."""
    from models import Base  # import local et évite un cycle

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Supprime toutes les tables ORM."""
    from models import Base

    Base.metadata.drop_all(bind=engine)
