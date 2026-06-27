"""DTO d'une liaison origine→destination (V2.1)."""

from pydantic import BaseModel


class GeoPoint(BaseModel):
    lat: float
    lon: float


class Liaison(BaseModel):
    departure_city: str
    departure: GeoPoint
    arrival_city: str
    arrival: GeoPoint
    nb_trajets: int
    part_nuit: float  # 0..1
    distance_moy_km: float | None
    co2_moy_par_pkm: float | None
