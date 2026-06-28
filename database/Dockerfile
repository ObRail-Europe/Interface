# Image du module base de données ObRail.
# Tirée et lancée, elle provisionne le schéma PostgreSQL (tables, index, vues) via Alembic,
# SANS les CSV de data/. Le chargement des données est une commande séparée :
#   python -m obrail_database.etl.run --data-dir /data
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dépendances d'abord (cache de couche), puis le package.
COPY database/pyproject.toml database/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY database/ .
RUN mkdir -p /app/data
COPY data/*.csv /app/data/
RUN uv sync --frozen --no-dev

# Exécution en utilisateur non-root.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Provisionne le schéma (tables + index + vues matérialisées).
CMD ["alembic", "upgrade", "head"]
