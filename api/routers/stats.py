"""Endpoints statistiques de l'onglet « Vue d'ensemble »."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencies import get_overview_service
from schemas.jour_nuit import JourNuitSplit
from schemas.operateur import OperateurStat
from schemas.overview import OverviewKPI
from services.overview_service import OverviewService

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])

ServiceDep = Annotated[OverviewService, Depends(get_overview_service)]


@router.get("/overview", response_model=OverviewKPI, summary="Indicateurs-clés du réseau")
def get_overview(service: ServiceDep) -> OverviewKPI:
    return service.get_overview()


@router.get("/jour-nuit", response_model=JourNuitSplit, summary="Répartition jour / nuit")
def get_jour_nuit(service: ServiceDep) -> JourNuitSplit:
    return service.get_jour_nuit()


@router.get("/operateurs", response_model=list[OperateurStat], summary="Top opérateurs")
def get_operateurs(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 5,
) -> list[OperateurStat]:
    return service.get_top_operateurs(limit)
