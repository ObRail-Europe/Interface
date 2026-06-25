"""Fixtures de tests partagées."""

import os
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from config import settings
from models import Base


@pytest.fixture(scope="session")
def engine() -> Engine:
    """Moteur SQLAlchemy vers la base de test ; skip si PostgreSQL est indisponible."""
    url = os.environ.get("TEST_DATABASE_URL", settings.database_url)
    eng = create_engine(url, future=True)
    try:
        with eng.connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL indisponible — test d'intégration ignoré")
    Base.metadata.create_all(eng)  # idempotent : crée les tables manquantes
    return eng


@pytest.fixture
def session(engine: Engine) -> Generator[Session]:
    """Session transactionnelle : tout est annulé (rollback) après chaque test."""
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection)
    try:
        yield sess
    finally:
        sess.close()
        transaction.rollback()
        connection.close()
