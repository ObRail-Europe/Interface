"""Client de l'API ObRail — onglet « Explorateur de trajets »."""

from typing import Any, Protocol

from api.base import BaseHttpClient


class ExplorerClient(Protocol):
    """Accès aux données de l'onglet Explorateur de trajets."""

    def get_liaisons(self, limit: int) -> list[dict[str, Any]]: ...


class HttpExplorerClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_liaisons(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._get(f"/api/v1/trajets/liaisons?limit={limit}")
