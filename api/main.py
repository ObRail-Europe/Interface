"""Point d'entrée de l'API ObRail : fabrique d'application FastAPI."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from exceptions import ObRailError
from logging_config import configure_logging
from routers import carbone, clusters, qualite, stats, territoires, trajets

logger = logging.getLogger("obrail.api")
_request_logger = logging.getLogger("obrail.request")

# Sondes infra non journalisées en détail.
_QUIET_PATHS = {"/health", "/metrics"}


def create_app() -> FastAPI:
    """Assemble l'application (logs, métriques, routers, sondes). Testable et surchargeable."""
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="API REST ObRail Europe",
    )

    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]
    ) -> JSONResponse:
        """Journalise chaque requête (méthode, chemin, statut, latence)."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        if response.status_code >= 500:
            level = logging.WARNING
        elif request.url.path in _QUIET_PATHS:
            level = logging.DEBUG
        else:
            level = logging.INFO
        _request_logger.log(
            level,
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.exception_handler(ObRailError)
    async def handle_obrail_error(request: Request, exc: ObRailError) -> JSONResponse:
        """Erreur métier → réponse normalisée + log au niveau adapté."""
        level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
        logger.log(level, "domain error: %s", exc.detail, extra={"code": exc.code})
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code}
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        """Erreur non gérée → 500 normalisé + trace complète dans les logs."""
        logger.exception("unhandled error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500, content={"detail": "Erreur interne", "code": "internal_error"}
        )

    app.include_router(stats.router)
    app.include_router(trajets.router)
    app.include_router(carbone.router)
    app.include_router(territoires.router)
    app.include_router(clusters.router)
    app.include_router(qualite.router)

    @app.get("/health", tags=["infra"])
    def health() -> dict[str, str]:
        """Sonde de liveness."""
        return {"status": "ok"}

    # Métriques Prometheus (latence, taux d'erreurs, volumes) exposées sur /metrics.
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    logger.info("application ready", extra={"code": "startup"})
    return app


app = create_app()
