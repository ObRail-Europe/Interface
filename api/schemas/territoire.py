"""DTO de l'onglet « Territoires & couverture ferroviaire » (V6)."""

from pydantic import BaseModel

from schemas.liaison import GeoPoint


class VilleGeoPoint(BaseModel):
    """V6.1 — commune géolocalisée et la valeur de la dimension cartographiée."""

    citycode: str
    city_name: str
    geo: GeoPoint
    population: float | None
    valeur: float | None  # valeur de la dimension demandée (gare, accessibilité, trajets…)
    has_gare: bool | None
