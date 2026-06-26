"""Endpoints de l'onglet « Explorateur de trajets »."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dependencies import get_explorer_service
from schemas.liaison import Liaison
from services.explorer_service import ExplorerService

router = APIRouter(prefix="/api/v1/trajets", tags=["trajets"])

ServiceDep = Annotated[ExplorerService, Depends(get_explorer_service)]


@router.get("/liaisons", response_model=list[Liaison], summary="Liaisons origine→destination")
def get_liaisons(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=2000)] = 100,
) -> list[Liaison]:
    return service.get_liaisons(limit)
