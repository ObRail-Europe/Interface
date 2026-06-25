# ObRail Europe - Plateforme ferroviaire (MSPR TPRE532)

Solution applicative conteneurisée pour **ObRail Europe**, observatoire du ferroviaire et de la mobilité
bas-carbone. Elle expose les données de **trajets** ferroviaires, de **villes** et un modèle de **clustering de
fragilité**, via une API REST et un dashboard. Ce dépôt correspond à la phase d'**industrialisation** du prototype.

> **État actuel : socle MVP** ; API et dashboard fonctionnent et sont conteneurisés

## Architecture

```
┌────────────┐      HTTP       ┌──────────┐      SQL       ┌────────────┐
│ dashboard  │ ──────────────▶ │   api    │ ─────────────▶ │ PostgreSQL │
│ Dash/Plotly│   API_URL       │ FastAPI  │  DATABASE_URL  │            │
│  :8050     │                 │  :8000   │                │   :5432    │
└────────────┘                 └──────────┘                └────────────┘
```

| Service     | Stack                       | Port  | Rôle                                            |
| ----------- | --------------------------- | ----- | ----------------------------------------------- |
| `db`        | PostgreSQL 16               | 5432  | Persistance des données (volume `pgdata`)       |
| `api`       | FastAPI + SQLAlchemy (uv)   | 8000  | API REST, doc OpenAPI/Swagger sur `/docs`       |
| `dashboard` | Dash / Plotly (uv)          | 8050  | Interface de consultation et de visualisation   |

## Démarrage rapide (une seule commande)

```bash
cp .env.example .env
docker compose up --build
```

- API : http://localhost:8000/health · Swagger : http://localhost:8000/docs
- Dashboard : http://localhost:8050

## Développement local (par service)

Chaque service est un projet Python 3.13 géré par [`uv`](https://docs.astral.sh/uv/).

```bash
cd api          # ou: cd dashboard
uv sync               # installe les dépendances (crée .venv + uv.lock)
uv run pytest         # tests
uv run ruff check     # lint
uv run ruff format    # formatage
uv run uvicorn main:app --reload      # API en local (port 8000)
# uv run python main.py                # Dashboard en local (port 8050)
```

## Structure

```
Interface/
├── docker-compose.yml      # orchestration db + api + dashboard
├── .env.example            # variables d'environnement (modèle)
├── api/                    # backend FastAPI
│   ├── main.py             # app + GET /health
│   ├── config.py           # settings (pydantic-settings)
│   ├── database.py         # moteur/session SQLAlchemy
│   └── tests/
├── dashboard/              # frontend Dash
│   ├── main.py             # app Dash + server (gunicorn)
│   └── tests/
├── data/                   # CSV + modèle .joblib (non versionnés)
└── .github/workflows/ci.yml
```

## Qualité & workflow

- **CI** : GitHub Actions (`.github/workflows/ci.yml`) - lint, tests, build des images Docker.
- **Lint/format** : `ruff` (config par service). **Hooks** : `pre-commit` (`.pre-commit-config.yaml`).
- **Branches** : GitHub Flow - `feat/…`, `fix/…` → PR → CI verte → revue → merge sur `main`.
- **Commits** : [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `ci:`, `docs:`…).
- **Secrets** : `.env` local (gitignored), GitHub Secrets en CI. Jamais de secret commité.

## Feuille de route

Phase features (sessions ultérieures) :

- **API** : `/trajets`, `/trajets/{id}`, `/stats/volumes`, `/stats/jour-nuit`, `/villes`, `/clusters`, `/fragilite`…
- **Dashboard** : pages Vue d'ensemble, Trajets, Jour/Nuit, Opérateurs, Carbone/CO₂, Villes & couverture,
  Fragilité/Clusters.
- **ETL** : ingestion des CSV (`data/`) dans PostgreSQL (`villes`, `clusters`, `trajets`).
- **Monitoring** : Prometheus + Grafana. **Tests E2E** : Playwright.
