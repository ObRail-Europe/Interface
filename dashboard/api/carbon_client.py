"""Client de l'API ObRail - onglet « Empreinte carbone ».

`CarbonClient` est l'abstraction dont dépend la page ; `HttpCarbonClient`
en est l'implémentation HTTP. Les tests injectent une doublure.
"""

from typing import Any, Protocol

from api.base import BaseHttpClient


class CarbonClient(Protocol):
    """Accès aux données de l'onglet Empreinte carbone."""

    def get_comparaison(self, facteur_avion_g_par_pkm: float | None = None) -> dict[str, Any]: ...

    def get_density(self) -> dict[str, Any]: ...

    def get_distribution(self) -> dict[str, Any]: ...


class HttpCarbonClient(BaseHttpClient):
    """Implémentation HTTP basée sur `requests`."""

    def get_comparaison(self, facteur_avion_g_par_pkm: float | None = None) -> dict[str, Any]:
        path = "/api/v1/stats/co2/comparaison-avion"
        if facteur_avion_g_par_pkm is not None:
            path += f"?facteur_avion_g_par_pkm={facteur_avion_g_par_pkm}"
        return self._get(path)

    def get_density(self) -> dict[str, Any]:
        return self._get("/api/v1/stats/co2/scatter")

    def get_distribution(self) -> dict[str, Any]:
        return self._get("/api/v1/stats/co2/par-mode")
