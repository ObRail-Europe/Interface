"""Endpoints de l'onglet « Explorateur de trajets »."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencies import get_explorer_service
from schemas.distance import DistanceHistogram
from schemas.liaison import Liaison
from schemas.trajet import TrajetPage, TripFilter
from services.explorer_service import ExplorerService

router = APIRouter(prefix="/api/v1/trajets", tags=["trajets"])

ServiceDep = Annotated[ExplorerService, Depends(get_explorer_service)]


def get_trip_filter(
    mode: str | None = None,
    is_night: bool | None = None,
    departure_city: str | None = None,
    arrival_city: str | None = None,
    agency_name: str | None = None,
    departure_country: str | None = None,
    arrival_country: str | None = None,
    distance_min_km: float | None = None,
    distance_max_km: float | None = None,
) -> TripFilter:
    """Dépendance : expose les filtres comme query params individuels."""
    return TripFilter(**locals())  # locals() = uniquement les paramètres ci-dessus


FilterDep = Annotated[TripFilter, Depends(get_trip_filter)]


@router.get("/liaisons", response_model=list[Liaison], summary="Liaisons origine→destination")
def get_liaisons(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=2000)] = 100,
) -> list[Liaison]:
    return service.get_liaisons(limit)


@router.get("/distances", response_model=DistanceHistogram, summary="Histogramme des distances")
def get_distance_histogram(
    service: ServiceDep,
    bin_km: Annotated[int, Query(ge=25, le=1000)] = 100,
) -> DistanceHistogram:
    return service.get_distance_histogram(bin_km)


@router.get("", response_model=TrajetPage, summary="Liste paginée et filtrable des trajets")
def list_trajets(
    service: ServiceDep,
    criteria: FilterDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    sort: str = "id",
) -> TrajetPage:
    return service.list_trajets(criteria, sort, page, page_size)
