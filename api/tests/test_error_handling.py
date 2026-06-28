"""Tests des handlers d'erreurs normalisées (ApiError)."""

import pytest
from fastapi.testclient import TestClient

from config import settings
from dependencies import _load_model
from main import app


def test_health_ok() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_domain_error_returns_normalized_apierror(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force l'indisponibilité du modèle → ModelUnavailableError → 503 normalisé.
    _load_model.cache_clear()
    monkeypatch.setattr(settings, "model_dir", "/nonexistent-model-dir")
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/api/v1/fragilite/predict", json={"has_gare": True})
        assert response.status_code == 503
        body = response.json()
        assert body["code"] == "model_unavailable"
        assert "detail" in body
    finally:
        _load_model.cache_clear()
