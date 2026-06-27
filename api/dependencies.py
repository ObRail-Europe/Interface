"""Injection de dépendances.

Les fournisseurs ci-dessous assemblent repository → service ; ils sont surchargeables
en test via `app.dependency_overrides`.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from repositories.carbon_repository import SqlAlchemyCarbonRepository
from repositories.interfaces import (
    CarbonRepository,
    StatsRepository,
    TerritoireRepository,
    TrajetRepository,
)
from repositories.stats_repository import SqlAlchemyStatsRepository
from repositories.territoire_repository import SqlAlchemyTerritoireRepository
from repositories.trajet_repository import SqlAlchemyTrajetRepository
from services.carbon_service import CarbonService
from services.explorer_service import ExplorerService
from services.overview_service import OverviewService
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
