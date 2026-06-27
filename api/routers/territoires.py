"""Endpoints de l'onglet « Territoires & couverture ferroviaire » (V6)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from dependencies import get_territoire_service
from schemas.territoire import AmplitudeDistribution, Couverture, VilleGeoPoint
from services.territoire_service import TerritoireService

# Préfixe large : l'onglet expose des routes sous /villes et sous /stats.
router = APIRouter(prefix="/api/v1", tags=["territoires"])

ServiceDep = Annotated[TerritoireService, Depends(get_territoire_service)]

Dimension = Literal["nb_trajets_total", "has_gare", "accessibilite_ord", "dist_gare_min_m"]
Maille = Literal["code_dept", "code_region"]


@router.get("/villes/carte", response_model=list[VilleGeoPoint], summary="Carte de la couverture")
def get_villes_carte(
    service: ServiceDep,
    dimension: Dimension = "nb_trajets_total",
    code_dept: str | None = None,
    code_region: str | None = None,
    has_gare: bool | None = None,
) -> list[VilleGeoPoint]:
    return service.get_carte(dimension, code_dept, code_region, has_gare)


@router.get("/stats/couverture", response_model=Couverture, summary="Couverture par maille")
def get_couverture(service: ServiceDep, by: Maille = "code_dept") -> Couverture:
    return service.get_couverture(by)


@router.get(
    "/stats/amplitude", response_model=AmplitudeDistribution, summary="Amplitude de service"
)
def get_amplitude(
    service: ServiceDep,
    bin_h: Annotated[float, Query(ge=0.5, le=6)] = 1.0,
) -> AmplitudeDistribution:
    return service.get_amplitude(bin_h)
