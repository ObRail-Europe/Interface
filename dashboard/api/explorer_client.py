"""Client de l'API ObRail — onglet « Explorateur de trajets »."""

from typing import Any, Protocol
from urllib.parse import urlencode

from api.base import BaseHttpClient


class ExplorerClient(Protocol):
    """Accès aux données de l'onglet Explorateur de trajets."""

    def get_liaisons(self, limit: int) -> list[dict[str, Any]]: ...

    def list_trajets(
        self, filters: dict[str, Any], sort: str, page: int, page_size: int
    ) -> dict[str, Any]: ...

    def get_distance_histogram(self, bin_km: int) -> dict[str, Any]: ...

    def get_trajet(self, trajet_id: int) -> dict[str, Any]: ...


class HttpExplorerClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_liaisons(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._get(f"/api/v1/trajets/liaisons?limit={limit}")

    def list_trajets(
        self, filters: dict[str, Any], sort: str = "id", page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        params = [(key, value) for key, value in filters.items() if value not in (None, "")]
        params += [("sort", sort), ("page", page), ("page_size", page_size)]
        return self._get(f"/api/v1/trajets?{urlencode(params)}")

    def get_distance_histogram(self, bin_km: int = 100) -> dict[str, Any]:
        return self._get(f"/api/v1/trajets/distances?bin_km={bin_km}")

    def get_trajet(self, trajet_id: int) -> dict[str, Any]:
        return self._get(f"/api/v1/trajets/{trajet_id}")
