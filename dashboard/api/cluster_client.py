"""Client de l'API ObRail — onglet « Fragilité territoriale ».

`ClusterClient` est l'abstraction dont dépend la page ; `HttpClusterClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol
from urllib.parse import urlencode

from api.base import BaseHttpClient


class ClusterClient(Protocol):
    """Accès aux données de l'onglet Fragilité territoriale."""

    def get_carte(
        self, code_dept: str | None = None, code_region: str | None = None
    ) -> list[dict[str, Any]]: ...

    def get_summaries(self) -> list[dict[str, Any]]: ...

    def get_profils(self) -> list[dict[str, Any]]: ...


class HttpClusterClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_carte(
        self, code_dept: str | None = None, code_region: str | None = None
    ) -> list[dict[str, Any]]:
        query = {k: v for k, v in (("code_dept", code_dept), ("code_region", code_region)) if v}
        suffix = f"?{urlencode(query)}" if query else ""
        return self._get(f"/api/v1/clusters/carte{suffix}")

    def get_summaries(self) -> list[dict[str, Any]]:
        return self._get("/api/v1/clusters")

    def get_profils(self) -> list[dict[str, Any]]:
        return self._get("/api/v1/clusters/profils")
