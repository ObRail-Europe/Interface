"""Client de l'API ObRail — onglet « Qualité des données ».

`QualiteClient` est l'abstraction dont dépend la page ; `HttpQualiteClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol
from urllib.parse import urlencode

from api.base import BaseHttpClient


class QualiteClient(Protocol):
    """Accès aux données de l'onglet Qualité des données."""

    def get_completude(self, table: str) -> dict[str, Any]: ...

    def get_anomalies(self) -> dict[str, Any]: ...

    def get_volumetrie(self) -> dict[str, Any]: ...


class HttpQualiteClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_completude(self, table: str = "trajets") -> dict[str, Any]:
        return self._get(f"/api/v1/qualite/completude?{urlencode({'table': table})}")

    def get_anomalies(self) -> dict[str, Any]:
        return self._get("/api/v1/qualite/anomalies")

    def get_volumetrie(self) -> dict[str, Any]:
        return self._get("/api/v1/qualite/volumetrie")
