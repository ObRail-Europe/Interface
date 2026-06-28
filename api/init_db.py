"""Initialise le schéma PostgreSQL : crée les tables ORM.

Usage (base lancée via docker compose) :  uv run python init_db.py
"""

import logging

from config import settings
from database import init_db
from logging_config import configure_logging

logger = logging.getLogger("obrail.init_db")

if __name__ == "__main__":
    configure_logging(settings.log_level)
    init_db()
    logger.info("schema initialized: ORM tables created")
