"""DTO transverses de l'API."""

from pydantic import BaseModel


class ApiError(BaseModel):
    """Réponse d'erreur normalisée (statuts 4xx/5xx)."""

    detail: str
    code: str
    field: str | None = None
