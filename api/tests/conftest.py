"""Fixtures de tests partagées."""

import os
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from config import settings
from models import Base


def _test_url() -> URL:
    raw = os.environ.get("TEST_DATABASE_URL")
    if raw:
        return make_url(raw)
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_test")


def _ensure_database(url: URL) -> None:
    """Crée la base de test si elle n'existe pas (connexion à la base 'postgres')."""
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Engine:
    """Moteur SQLAlchemy vers la base de test ; skip si PostgreSQL est indisponible."""
    url = _test_url()
    try:
        _ensure_database(url)
        eng = create_engine(url, future=True)
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
