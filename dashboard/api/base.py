"""Client HTTP de base : logique de requête partagée par les clients de l'API."""

import logging
from typing import Any

import requests

logger = logging.getLogger("obrail.dashboard.api")


class BaseHttpClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(method, url, timeout=self._timeout, **kwargs)
            response.raise_for_status()
        except requests.RequestException:
            logger.warning("API request failed: %s %s", method, path)
            raise
        return response.json()

    def _get(self, path: str) -> Any:
        return self._request("GET", path)

    def _post(self, path: str, json: Any) -> Any:
        return self._request("POST", path, json=json)
