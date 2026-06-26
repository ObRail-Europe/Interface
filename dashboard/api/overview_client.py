"""Client de l'API ObRail — onglet « Vue d'ensemble ».

`OverviewClient` est l'abstraction dont dépend la page ; `HttpOverviewClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol

from api.base import BaseHttpClient


class OverviewClient(Protocol):
    """Accès aux données de l'onglet Vue d'ensemble."""

    def get_overview(self) -> dict[str, Any]: ...

    def get_jour_nuit(self) -> dict[str, Any]: ...

    def get_operateurs(self, limit: int) -> list[dict[str, Any]]: ...

    def get_departs(self) -> list[dict[str, Any]]: ...


class HttpOverviewClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_overview(self) -> dict[str, Any]:
        return self._get("/api/v1/stats/overview")

    def get_jour_nuit(self) -> dict[str, Any]:
        return self._get("/api/v1/stats/jour-nuit")

    def get_operateurs(self, limit: int = 5) -> list[dict[str, Any]]:
        return self._get(f"/api/v1/stats/operateurs?limit={limit}")

    def get_departs(self) -> list[dict[str, Any]]:
        return self._get("/api/v1/stats/departs")
