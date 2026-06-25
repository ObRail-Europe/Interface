"""Configuration du dashboard."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_url: str = os.environ.get("API_URL", "http://localhost:8000")


settings = Settings()
