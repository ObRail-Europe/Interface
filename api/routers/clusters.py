"""Endpoints de l'onglet « Fragilité territoriale » (V7)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_fragilite_model, get_fragilite_service
from ml.fragilite_model import FragiliteModel
from schemas.fragilite import (
    ClusterGeoPoint,
    ClusterProfil,
    ClusterSummary,
    FragiliteFeatures,
    FragilitePrediction,
)
from services.fragilite_service import FragiliteService

# Préfixe large : routes sous /clusters et /fragilite (cf. spec).
router = APIRouter(prefix="/api/v1", tags=["fragilite"])

ServiceDep = Annotated[FragiliteService, Depends(get_fragilite_service)]
ModelDep = Annotated[FragiliteModel, Depends(get_fragilite_model)]


@router.get("/clusters/carte", response_model=list[ClusterGeoPoint], summary="Carte des clusters")
def get_clusters_carte(
    service: ServiceDep,
    code_dept: str | None = None,
    code_region: str | None = None,
    has_gare: bool | None = None,
) -> list[ClusterGeoPoint]:
    return service.get_carte(code_dept, code_region, has_gare)


@router.get("/clusters", response_model=list[ClusterSummary], summary="Effectifs des clusters")
def get_clusters(service: ServiceDep) -> list[ClusterSummary]:
    return service.get_summaries()


@router.get("/clusters/profils", response_model=list[ClusterProfil], summary="Profils des clusters")
def get_clusters_profils(service: ServiceDep) -> list[ClusterProfil]:
    return service.get_profils()


@router.post(
    "/fragilite/predict", response_model=FragilitePrediction, summary="Simulateur de fragilité"
)
def predict_fragilite(model: ModelDep, features: FragiliteFeatures) -> FragilitePrediction:
    result = model.predict(features.model_dump(exclude={"has_gare"}), features.has_gare)
    return FragilitePrediction(
        cluster=result.cluster,
        cluster_nom=result.cluster_nom,
        niveau_fragilite=result.niveau_fragilite,
    )
