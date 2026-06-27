"""Client HTTP de base : logique de requête partagée par les clients de l'API."""

from typing import Any

import requests


class BaseHttpClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _get(self, path: str) -> Any:
        response = requests.get(f"{self._base_url}{path}", timeout=self._timeout)
        response.raise_for_status()
        return response.json()
