"""Point d'entrée de l'API ObRail.

MVP : application FastAPI fonctionnelle exposant uniquement la sonde /health.
"""

from fastapi import FastAPI

from config import settings

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API REST ObRail Europe",
)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    """Sonde de liveness"""
    return {"status": "ok"}
