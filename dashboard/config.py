"""Configuration du dashboard."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_url: str = os.environ.get("API_URL", "http://localhost:8000")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    # URL Grafana exposée au navigateur pour les panneaux embarqués (onglet Supervision).
    grafana_url: str = os.environ.get("GRAFANA_URL", "http://localhost:3000")


settings = Settings()
