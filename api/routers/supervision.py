"""Endpoints de l'onglet « Supervision » (V9.1 — santé détaillée)."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas.supervision import HealthDetails, ServiceHealth

router = APIRouter(prefix="/api/v1/health", tags=["supervision"])

logger = logging.getLogger("obrail.supervision")


@router.get("/details", response_model=HealthDetails, summary="État de santé détaillé")
def health_details(db: Annotated[Session, Depends(get_db)]) -> HealthDetails:
    """État des services (API + base) avec latence — alimente les badges UP/DOWN."""
    services = [ServiceHealth(nom="api", statut="up", latence_ms=0.0)]

    start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        statut = "up"
    except Exception:
        logger.warning("database health check failed", extra={"code": "db_down"})
        statut = "down"
    latence_ms = round((time.perf_counter() - start) * 1000, 1)
    services.append(ServiceHealth(nom="database", statut=statut, latence_ms=latence_ms))

    return HealthDetails(services=services)
