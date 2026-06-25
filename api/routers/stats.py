"""Endpoints statistiques de l'onglet « Vue d'ensemble »."""

from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_overview_service
from schemas.overview import OverviewKPI
from services.overview_service import OverviewService

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewKPI, summary="Indicateurs-clés du réseau")
def get_overview(service: Annotated[OverviewService, Depends(get_overview_service)]) -> OverviewKPI:
    return service.get_overview()
