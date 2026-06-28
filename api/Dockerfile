# Image de l'API. Build depuis la RACINE du dépôt (contexte .) car l'api dépend du module
# `database` par chemin éditable :  docker build -f api/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/api/.venv/bin:$PATH"

WORKDIR /app

# Le module database (dépendance path) doit être présent pour résoudre `../database`.
COPY database/ /app/database/
COPY api/pyproject.toml api/uv.lock /app/api/

WORKDIR /app/api
RUN uv sync --frozen --no-dev

COPY api/ /app/api/

# Exécution en utilisateur non-root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
