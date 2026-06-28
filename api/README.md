# api — backend FastAPI ObRail

API REST de la plateforme ObRail Europe : expose les données ferroviaires, territoriales et le
**modèle de fragilité** (simulateur live). Projet uv indépendant ; lit PostgreSQL via les **modèles
ORM du module `obrail-database`** (dépendance path éditable). Doc OpenAPI/Swagger sur `/docs`.

## Architecture en couches (clean architecture)

Câblage `router → service → repository → session`, avec **inversion de dépendance** (les services
dépendent de `Protocol`, pas de SQLAlchemy) — d'où une testabilité fine.

| Couche | Dossier | Rôle |
| --- | --- | --- |
| Présentation | `routers/` | contrôleurs HTTP (FastAPI), validation, statuts |
| Service | `services/` | cas d'usage métier (ratios, conversions, assemblage des DTO) |
| Accès données | `repositories/` | `Protocol` (`interfaces.py`) + implémentation SQLAlchemy (lecture des vues) |
| Contrats | `schemas/` | DTO Pydantic v2 |
| Modèle ML | `ml/` | inférence du modèle de fragilité (`cluster_fragilite.joblib`, numpy pur) |
| Injection | `dependencies.py` | assemble repository → service ; surchargeable en test |

`main.py` (`create_app()`) monte les routers, la sonde `GET /health`, l'instrumentation Prometheus
(`/metrics`), le middleware de logs et les handlers d'erreurs.

## Endpoints (par onglet du dashboard)

| Onglet | Endpoints |
| --- | --- |
| Vue d'ensemble (V1) | `GET /api/v1/stats/{overview,jour-nuit,operateurs,departs}` |
| Explorateur (V2) | `GET /api/v1/trajets`, `/trajets/{id}`, `/trajets/liaisons`, `/trajets/distances` |
| Empreinte carbone (V5) | `GET /api/v1/stats/co2/{comparaison-avion,scatter,par-mode}` |
| Territoires (V6) | `GET /api/v1/villes/carte`, `/stats/{couverture,amplitude}` |
| Fragilité (V7) | `GET /api/v1/clusters{,/carte,/profils}`, `/stats/fragilite`, **`POST /api/v1/fragilite/predict`** |
| Qualité (V8) | `GET /api/v1/qualite/{completude,anomalies,volumetrie}` |
| Supervision (V9) | `GET /health`, `/api/v1/health/details`, `/metrics` |

> **Performance** : les agrégations sur ~13M trajets lisent des **vues matérialisées** précalculées
> (définies dans `obrail-database`) ; les lectures ligne-à-ligne s'appuient sur les index existants.

## Observabilité & robustesse

- **Logs structurés JSON** sur stdout (`logging_config.py`, niveau via `LOG_LEVEL`) — collectés par Loki.
- **Middleware** journalisant chaque requête (méthode, chemin, statut, latence).
- **Erreurs normalisées** : exceptions métier (`exceptions.py`) → réponse `ApiError { detail, code }`.
- **Métriques Prometheus** (`/metrics`) : latence, taux d'erreurs, volumes.

## Configuration (env)

`DATABASE_URL` · `MODEL_DIR` (dossier des `.joblib`, défaut `../data`) · `LOG_LEVEL` ·
`API_TITLE` / `API_VERSION`. Voir `config.py` (pydantic-settings).

## Développement

```bash
uv sync                               # installe les deps (dont obrail-database en path éditable)
uv run uvicorn main:app --reload      # API locale sur :8000
uv run pytest -q                      # tests (PostgreSQL requis)
uv run ruff check && uv run ruff format
```

**Tests** : services testés avec des **doublures en mémoire** (sans base) ; endpoints testés via
`TestClient` sur une **base seed** (fixtures du plugin `obrail_database.testing`, override de `get_db`).
Le simulateur de fragilité est testé contre le vrai `.joblib` (ignoré si absent).

## Conteneurisation

`api/Dockerfile` se build depuis la **racine du dépôt** (`docker build -f api/Dockerfile .`) car
l'image embarque le module `database` (dépendance path). Dans la stack, le service `api` en dépend
(`build: { context: ., dockerfile: api/Dockerfile }`).
