"""Cas d'usage de l'onglet « Territoires & couverture ferroviaire »."""

from repositories.interfaces import TerritoireRepository
from schemas.liaison import GeoPoint
from schemas.territoire import VilleGeoPoint


class TerritoireService:
    """Construit les données territoriales à partir du repository."""

    def __init__(self, repository: TerritoireRepository) -> None:
        self._repository = repository

    def get_carte(
        self,
        dimension: str,
        code_dept: str | None = None,
        code_region: str | None = None,
        has_gare: bool | None = None,
    ) -> list[VilleGeoPoint]:
        """V6.1 — communes géolocalisées et la valeur de la dimension cartographiée."""
        return [
            VilleGeoPoint(
                citycode=v.citycode,
                city_name=v.city_name,
                geo=GeoPoint(lat=v.lat, lon=v.lon),
                population=v.population,
                valeur=v.valeur,
                has_gare=v.has_gare,
            )
            for v in self._repository.villes_carte(dimension, code_dept, code_region, has_gare)
        ]
