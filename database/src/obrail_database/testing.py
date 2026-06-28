"""Plugin pytest partagé : fixtures de base de test (moteur + jeux de données seed).

Réutilisé par les tests du module `database` **et** de l'`api` via
`pytest_plugins = ("obrail_database.testing",)`. Importe `pytest` : à n'utiliser
qu'en contexte de test (jamais au runtime).
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from obrail_database.config import settings
from obrail_database.etl.loaders import load_clusters, load_trajets, load_villes, truncate_all
from obrail_database.etl.resolve import resolve_clusters, resolve_trajets
from obrail_database.etl.views import ALL_VIEWS, create_views, drop_views, refresh_views
from obrail_database.models import Base

# Jeux de données seed embarqués dans le package (CSV de petite taille).
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


def _seed(engine: Engine, *, with_flights: bool) -> Session:
    """Charge le jeu seed (villes, clusters, trajets [+ vols]), résout, rafraîchit les vues."""
    with Session(engine) as setup:
        truncate_all(setup)
        load_villes(setup, FIXTURES / "villes_sample.csv")
        load_clusters(setup, FIXTURES / "clusters_sample.csv")
        setup.commit()
    load_trajets(engine, FIXTURES / "trajets_sample.parquet")
    if with_flights:
        load_trajets(engine, FIXTURES / "trajets_flights_sample.parquet")
    with Session(engine) as setup:
        resolve_clusters(setup)
        resolve_trajets(setup)
        setup.commit()
    refresh_views(engine)
    return Session(engine)


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
        pytest.skip("PostgreSQL indisponible - test d'intégration ignoré")
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
    """Base peuplée du jeu seed (train-only), nettoyée après le test."""
    sess = _seed(engine, with_flights=False)
    try:
        yield sess
    finally:
        sess.close()
        with Session(engine) as cleanup:
            truncate_all(cleanup)
            cleanup.commit()


@pytest.fixture
def carbon_session(engine: Engine) -> Generator[Session]:
    """Seed enrichi de vols (`train` + `flight`) pour l'onglet « Empreinte carbone »."""
    sess = _seed(engine, with_flights=True)
    try:
        yield sess
    finally:
        sess.close()
        with Session(engine) as cleanup:
            truncate_all(cleanup)
            cleanup.commit()
