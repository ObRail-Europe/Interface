"""Client de l'API ObRail — onglet « Territoires & couverture ferroviaire ».

`TerritoireClient` est l'abstraction dont dépend la page ; `HttpTerritoireClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol
from urllib.parse import urlencode

from api.base import BaseHttpClient


class TerritoireClient(Protocol):
    """Accès aux données de l'onglet Territoires & couverture."""

    def get_carte(
        self,
        dimension: str,
        code_dept: str | None = None,
        code_region: str | None = None,
        has_gare: bool | None = None,
    ) -> list[dict[str, Any]]: ...


class HttpTerritoireClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_carte(
        self,
        dimension: str = "nb_trajets_total",
        code_dept: str | None = None,
        code_region: str | None = None,
        has_gare: bool | None = None,
    ) -> list[dict[str, Any]]:
        params = {"dimension": dimension, "code_dept": code_dept, "code_region": code_region}
        query = {k: v for k, v in params.items() if v not in (None, "")}
        if has_gare is not None:
            query["has_gare"] = str(has_gare).lower()
        return self._get(f"/api/v1/villes/carte?{urlencode(query)}")
