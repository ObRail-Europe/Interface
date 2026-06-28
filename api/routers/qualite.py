"""Endpoints de l'onglet « Qualité des données » (V8)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from dependencies import get_qualite_service
from schemas.qualite import Anomalies, Completude, Volumetrie
from services.qualite_service import QualiteService

router = APIRouter(prefix="/api/v1/qualite", tags=["qualite"])

ServiceDep = Annotated[QualiteService, Depends(get_qualite_service)]

Table = Literal["trajets", "villes", "clusters"]


@router.get("/completude", response_model=Completude, summary="Complétude par colonne")
def get_completude(service: ServiceDep, table: Table = "trajets") -> Completude:
    return service.get_completude(table)


@router.get("/anomalies", response_model=Anomalies, summary="Anomalies & doublons")
def get_anomalies(service: ServiceDep) -> Anomalies:
    return service.get_anomalies()


@router.get("/volumetrie", response_model=Volumetrie, summary="Volumétrie par source")
def get_volumetrie(service: ServiceDep) -> Volumetrie:
    return service.get_volumetrie()
