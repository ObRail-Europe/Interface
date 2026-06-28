"""DTO de l'onglet « Supervision » (V9)."""

from pydantic import BaseModel


class ServiceHealth(BaseModel):
    """État d'un service et sa latence de réponse."""

    nom: str
    statut: str  # up | down
    latence_ms: float


class HealthDetails(BaseModel):
    """V9.1 — état de santé détaillé des services."""

    services: list[ServiceHealth]
