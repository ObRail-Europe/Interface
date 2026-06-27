"""Fixtures de tests partagées."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from config import settings
from etl.loaders import load_clusters, load_trajets, load_villes, truncate_all
from etl.resolve import resolve_clusters, resolve_trajets
from etl.views import ALL_VIEWS, create_views, drop_views, refresh_views
from models import Base

FIXTURES = Path(__file__).parent / "fixtures"


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
    with eng.begin() as connection:  # vues matérialisées (recréées : reflètent la définition)
        drop_views(connection, ALL_VIEWS)
        create_views(connection, ALL_VIEWS)
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


@pytest.fixture
def seeded_session(engine: Engine) -> Generator[Session]:
    """Base peuplée du jeu de données seed (ingestion + résolution), nettoyée après le test.

    Réutilisable par les futurs tests d'endpoints (et la CI : `data/` n'y est pas présent).
    """
    with Session(engine) as setup:
        truncate_all(setup)
        load_villes(setup, FIXTURES / "villes_sample.csv")
        load_clusters(setup, FIXTURES / "clusters_sample.csv")
        setup.commit()
    load_trajets(engine, FIXTURES / "trajets_sample.csv")
    with Session(engine) as setup:
        resolve_clusters(setup)
        resolve_trajets(setup)
        setup.commit()
    refresh_views(engine)  # les vues matérialisées reflètent le seed

    sess = Session(engine)
    try:
        yield sess
    finally:
        sess.close()
        with Session(engine) as cleanup:
            truncate_all(cleanup)
            cleanup.commit()


@pytest.fixture
def client(seeded_session: Session) -> Generator:
    """Client HTTP de test : l'API requête la base seed (override de get_db)."""
    from fastapi.testclient import TestClient

    from database import get_db
    from main import app

    def _override_get_db() -> Generator[Session]:
        yield seeded_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def carbon_session(engine: Engine) -> Generator[Session]:
    """Seed enrichi de vols (`train` + `flight`) pour l'onglet « Empreinte carbone ».

    Les endpoints carbone comparent les deux modes : le seed standard est train-only,
    on lui ajoute donc un échantillon de vols avant de rafraîchir les vues.
    """
    with Session(engine) as setup:
        truncate_all(setup)
        load_villes(setup, FIXTURES / "villes_sample.csv")
        load_clusters(setup, FIXTURES / "clusters_sample.csv")
        setup.commit()
    load_trajets(engine, FIXTURES / "trajets_sample.csv")
    load_trajets(engine, FIXTURES / "trajets_flights_sample.csv")
    with Session(engine) as setup:
        resolve_clusters(setup)
        resolve_trajets(setup)
        setup.commit()
    refresh_views(engine)  # les vues matérialisées reflètent le seed train + vols

    sess = Session(engine)
    try:
        yield sess
    finally:
        sess.close()
        with Session(engine) as cleanup:
            truncate_all(cleanup)
            cleanup.commit()


@pytest.fixture
def carbon_client(carbon_session: Session) -> Generator:
    """Client HTTP de test branché sur le seed carbone (train + vols)."""
    from fastapi.testclient import TestClient

    from database import get_db
    from main import app

    def _override_get_db() -> Generator[Session]:
        yield carbon_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
