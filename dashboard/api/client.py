"""Client de l'API ObRail.

`OverviewClient` est l'abstraction dont dépendent les pages ; `HttpOverviewClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol

import requests


class OverviewClient(Protocol):
    """Accès aux données de l'onglet Vue d'ensemble."""

    def get_overview(self) -> dict[str, Any]: ...


class HttpOverviewClient:
    """Implémentation HTTP basée sur `requests`."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _get(self, path: str) -> Any:
        response = requests.get(f"{self._base_url}{path}", timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def get_overview(self) -> dict[str, Any]:
        return self._get("/api/v1/stats/overview")
