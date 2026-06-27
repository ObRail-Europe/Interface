"""Endpoints de l'onglet « Empreinte carbone » (train vs avion)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencies import get_carbon_service
from schemas.carbon import ComparaisonAvion
from services.carbon_service import CarbonService

router = APIRouter(prefix="/api/v1/stats/co2", tags=["carbone"])

ServiceDep = Annotated[CarbonService, Depends(get_carbon_service)]


@router.get("/comparaison-avion", response_model=ComparaisonAvion, summary="CO₂ évité vs avion")
def get_comparaison_avion(
    service: ServiceDep,
    facteur_avion_g_par_pkm: Annotated[float | None, Query(gt=0, le=1000)] = None,
) -> ComparaisonAvion:
    return service.get_comparaison(facteur_avion_g_par_pkm)
