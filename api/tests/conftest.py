"""Fixtures de tests de l'API : base seed (plugin partagé) + clients HTTP."""

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

# Fixtures de base (engine, seeded_session, carbon_session) fournies par le module database.
pytest_plugins = ("obrail_database.testing",)


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
