"""Injection de dépendances.

Les fournisseurs ci-dessous assemblent repository → service ; ils sont surchargeables
en test via `app.dependency_overrides`.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from repositories.interfaces import StatsRepository, TrajetRepository
from repositories.stats_repository import SqlAlchemyStatsRepository
from repositories.trajet_repository import SqlAlchemyTrajetRepository
from services.explorer_service import ExplorerService
from services.overview_service import OverviewService


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
