"""Initialise le schéma PostgreSQL : crée les tables ORM.

Prototypage uniquement ; en production le schéma est géré par Alembic
(`alembic upgrade head`). Usage : `uv run python -m obrail_database.init_db`.
"""

import logging

from obrail_database.config import settings
from obrail_database.engine import create_db_engine
from obrail_database.logging_config import configure_logging
from obrail_database.models import Base

logger = logging.getLogger("obrail.init_db")


def init_db() -> None:
    """Crée toutes les tables ORM dans la base."""
    Base.metadata.create_all(bind=create_db_engine())


if __name__ == "__main__":
    configure_logging(settings.log_level)
    init_db()
    logger.info("schema initialized: ORM tables created")
