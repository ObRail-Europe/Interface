"""Point d'entrée de l'API ObRail : fabrique d'application FastAPI."""

from fastapi import FastAPI

from config import settings
from routers import stats, trajets


def create_app() -> FastAPI:
    """Assemble l'application (routers, sonde santé). Testable et surchargeable."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="API REST ObRail Europe",
    )
    app.include_router(stats.router)
    app.include_router(trajets.router)

    @app.get("/health", tags=["infra"])
    def health() -> dict[str, str]:
        """Sonde de liveness."""
        return {"status": "ok"}

    return app


app = create_app()
