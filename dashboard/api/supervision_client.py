"""Client de l'API ObRail — onglet « Supervision » (V9.1)."""

from typing import Any, Protocol

from api.base import BaseHttpClient


class SupervisionClient(Protocol):
    """Accès à l'état de santé des services."""

    def get_health_details(self) -> dict[str, Any]: ...


class HttpSupervisionClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_health_details(self) -> dict[str, Any]:
        return self._get("/api/v1/health/details")
