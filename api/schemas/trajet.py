"""DTO de la liste paginée de trajets (V2.2)."""

from pydantic import BaseModel, ConfigDict


class TripFilter(BaseModel):
    """Filtres de la table des trajets."""

    mode: str | None = None
    is_night: bool | None = None
    departure_city: str | None = None
    arrival_city: str | None = None
    agency_name: str | None = None
    departure_country: str | None = None
    arrival_country: str | None = None
    distance_min_km: float | None = None
    distance_max_km: float | None = None


class TrajetListItem(BaseModel):
    """Ligne de la table."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: str | None
    mode: str | None
    agency_name: str | None
    route_short_name: str | None
    departure_city: str | None
    departure_country: str | None
    arrival_city: str | None
    arrival_country: str | None
    departure_time: str | None
    arrival_time: str | None
    distance_km: float | None
    is_night_train: bool | None
    emissions_co2: float | None
    co2_per_pkm: float | None


class TrajetPage(BaseModel):
    """Enveloppe de pagination."""

    items: list[TrajetListItem]
    total: int
    page: int
    page_size: int
    pages: int
