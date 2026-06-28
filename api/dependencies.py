"""Injection de dépendances.

Les fournisseurs ci-dessous assemblent repository → service ; ils sont surchargeables
en test via `app.dependency_overrides`.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from ml.fragilite_model import FragiliteModel, load_fragilite_model
from repositories.carbon_repository import SqlAlchemyCarbonRepository
from repositories.cluster_repository import SqlAlchemyClusterRepository
from repositories.interfaces import (
    CarbonRepository,
    ClusterRepository,
    QualiteRepository,
    StatsRepository,
    TerritoireRepository,
    TrajetRepository,
)
from repositories.qualite_repository import SqlAlchemyQualiteRepository
from repositories.stats_repository import SqlAlchemyStatsRepository
from repositories.territoire_repository import SqlAlchemyTerritoireRepository
from repositories.trajet_repository import SqlAlchemyTrajetRepository
from services.carbon_service import CarbonService
from services.explorer_service import ExplorerService
from services.fragilite_service import FragiliteService
from services.overview_service import OverviewService
from services.qualite_service import QualiteService
from services.territoire_service import TerritoireService


def get_stats_repository(session: Annotated[Session, Depends(get_db)]) -> StatsRepository:
    return SqlAlchemyStatsRepository(session)


def get_overview_service(
    repository: Annotated[StatsRepository, Depends(get_stats_repository)],
) -> OverviewService:
    return OverviewService(repository)


def get_trajet_repository(session: Annotated[Session, Depends(get_db)]) -> TrajetRepository:
    return SqlAlchemyTrajetRepository(session)


def get_explorer_service(
    repository: Annotated[TrajetRepository, Depends(get_trajet_repository)],
) -> ExplorerService:
    return ExplorerService(repository)


def get_carbon_repository(session: Annotated[Session, Depends(get_db)]) -> CarbonRepository:
    return SqlAlchemyCarbonRepository(session)


def get_carbon_service(
    repository: Annotated[CarbonRepository, Depends(get_carbon_repository)],
) -> CarbonService:
    return CarbonService(repository)


def get_territoire_repository(
    session: Annotated[Session, Depends(get_db)],
) -> TerritoireRepository:
    return SqlAlchemyTerritoireRepository(session)


def get_territoire_service(
    repository: Annotated[TerritoireRepository, Depends(get_territoire_repository)],
) -> TerritoireService:
    return TerritoireService(repository)


def get_cluster_repository(session: Annotated[Session, Depends(get_db)]) -> ClusterRepository:
    return SqlAlchemyClusterRepository(session)


def get_fragilite_service(
    repository: Annotated[ClusterRepository, Depends(get_cluster_repository)],
) -> FragiliteService:
    return FragiliteService(repository)


def get_qualite_repository(session: Annotated[Session, Depends(get_db)]) -> QualiteRepository:
    return SqlAlchemyQualiteRepository(session)


def get_qualite_service(
    repository: Annotated[QualiteRepository, Depends(get_qualite_repository)],
) -> QualiteService:
    return QualiteService(repository)


@lru_cache(maxsize=1)
def _load_model() -> FragiliteModel:
    """Charge le modèle une seule fois (artefacts .joblib, cf. settings.model_dir)."""
    return load_fragilite_model(settings.model_dir)


def get_fragilite_model() -> FragiliteModel:
    """Fournit le modèle live ; 503 si les artefacts sont absents (non bloquant pour les vues)."""
    try:
        return _load_model()
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Modèle de fragilité indisponible") from exc
