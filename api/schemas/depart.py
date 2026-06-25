"""DTO d'une ville de départ géolocalisée (V1.3)."""

from pydantic import BaseModel


class DepartPoint(BaseModel):
    citycode: str
    city_name: str
    lat: float
    lon: float
    nb_trajets: int
