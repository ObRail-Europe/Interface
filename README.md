# ObRail Europe - Plateforme ferroviaire (MSPR TPRE532)

Solution applicative conteneurisée pour **ObRail Europe**, observatoire du ferroviaire et de la mobilité
bas-carbone. Elle expose les données de **trajets** ferroviaires, de **villes** et un modèle de **clustering de
fragilité**, via une API REST et un dashboard. Ce dépôt correspond à la phase d'**industrialisation** du prototype.

> **État actuel** : socle MVP conteneurisé (API + dashboard) et **schéma de données** PostgreSQL (3 tables).
> Endpoints métier et ingestion ETL des données à venir.

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
docker compose up --build                    # db + migrations + api + dashboard
docker compose --profile load run --rm load  # (optionnel) ingère les CSV de data/
```

- API : http://localhost:8000/health · Swagger : http://localhost:8000/docs
- Dashboard : http://localhost:8050

> Le **schéma est créé automatiquement** au démarrage (service `migrate` → `alembic upgrade head`).
> Le chargement des données reste explicite (service `load`).

## Développement local (par service)

Chaque service est un projet Python 3.13 géré par [`uv`](https://docs.astral.sh/uv/).

```bash
cd api          # ou: cd dashboard
uv sync               # installe les dépendances (crée .venv + uv.lock)
uv run pytest         # tests (intégration : PostgreSQL requis, cf. § Base de données)
uv run ruff check     # lint
uv run ruff format    # formatage
uv run uvicorn main:app --reload      # API en local (port 8000)
# uv run python main.py                # Dashboard en local (port 8050)
```

## Base de données (schéma)

Trois tables PostgreSQL, alimentées par les fichiers de `data/` (modèles SQLAlchemy 2.0 dans `api/models/`) :

| Table | Source (`data/`) | Clé primaire | Contenu |
| --- | --- | --- | --- |
| `villes` | `villes_enriched.csv` (~10k) | `citycode` (INSEE) | desserte + indicateurs socio-éco par commune |
| `clusters` | `clusters_final.csv` (~10k) | `row_id` | cluster de fragilité + features (modèle `cluster_fragilite.joblib`) |
| `trajets` | `routes_france.csv` (~13M) | `id` (surrogate) | trajets ferroviaires : horaires, géo, calendrier, CO₂ |

**Schéma** : géré par Alembic, appliqué automatiquement dans la stack (service `migrate`). En local :

```bash
cd api
uv run alembic upgrade head          # applique les migrations
# uv run python init_db.py            # alternative create_all (tests / prototypage)
```

**Données** : ingestion des CSV + résolution des jointures inter-sources.

```bash
docker compose --profile load run --rm load   # dans la stack (data/ montée en lecture seule)
cd api && uv run python -m etl.run            # en local (base lancée)
#   options : --trajets-limit N · --skip-trajets · --skip-resolve
```

Choix de modélisation :

- **`trajets`** : clé technique `id` (BigInteger), car `trip_id` n'est pas garanti unique sur ~13M lignes.
- **Jointures résolues à l'ETL** : `clusters.citycode` par **coordonnées** (100 %) ;
  `trajets.departure/arrival_citycode` par **nom normalisé** (homonymes tranchés par gare puis population,
  alias Paris/Lyon/Marseille, ~50 % côté FR - étranger/quartiers non résolus assumés).
- **Heures GTFS** (ex. `24:29:00`, valides en GTFS mais hors plage SQL `TIME`) conservées en **texte** ;
  dates de service typées `Date`.

> Les **tests d'intégration** tournent sur une **base dédiée** (`TEST_DATABASE_URL`, sinon la base configurée
> suffixée `_test`, créée si absente) - isolée des données de dev. Ignorés si PostgreSQL est indisponible ;
> les tests de métadonnées tournent sans base.

## Structure

```
Interface/
├── docker-compose.yml      # orchestration db + api + dashboard
├── .env.example            # variables d'environnement (modèle)
├── api/                    # backend FastAPI (couches routers/services/repositories/schemas)
│   ├── main.py             # create_app() : routers + GET /health
│   ├── routers/            # contrôleurs HTTP
│   ├── services/           # cas d'usage métier
│   ├── repositories/       # accès données (Protocol + SQLAlchemy)
│   ├── schemas/            # DTO Pydantic
│   ├── dependencies.py     # injection de dépendances
│   ├── models/             # modèles ORM : Base, Ville, Cluster, Trajet
│   ├── etl/                # ingestion + résolution des jointures
│   ├── migrations/         # Alembic
│   └── tests/
├── dashboard/              # frontend Dash (couches api/components/pages)
│   ├── main.py             # create_app() : onglets + server (gunicorn)
│   ├── api/                # client de l'API (Protocol + HTTP)
│   ├── components/         # composants purs (KPI, graphiques)
│   ├── pages/              # onglets (layout + callbacks)
│   └── tests/
├── data/                   # CSV + modèle .joblib (non versionnés)
└── .github/workflows/ci.yml
```

## Architecture applicative (clean architecture)

Les deux services sont organisés en **couches** avec **inversion de dépendance** : les couches
métier dépendent d'abstractions (`Protocol`), pas d'implémentations - d'où une bonne testabilité.

**API** - câblage `router → service → repository → session` (via `dependencies.py`) :

| Couche | Dossier | Rôle |
| --- | --- | --- |
| Présentation | `routers/` | Contrôleurs HTTP (FastAPI), validation, statuts |
| Service | `services/` | Cas d'usage métier (ratios, conversions, assemblage des DTO) |
| Accès données | `repositories/` | `Protocol` + implémentation SQLAlchemy (agrégations SQL) |
| Contrats | `schemas/` | DTO Pydantic |

Les **services** sont testés avec des doublures en mémoire ; les **endpoints** avec une base seed.

**Dashboard** :

| Couche | Dossier | Rôle |
| --- | --- | --- |
| Infrastructure | `api/` | `OverviewClient` (`Protocol`) + client HTTP |
| Présentation | `components/` | Fonctions **pures** `données → composant/figure` (testables sans navigateur) |
| Page | `pages/` | Layout + callbacks (client injecté) |

## Onglet « Vue d'ensemble » (V1)

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V1.1 Bandeau de KPI | `GET /api/v1/stats/overview` | 8 cartes (trajets, % nuit, opérateurs, villes, pays, transfrontalier, distance médiane, CO₂) |
| V1.2 Donut jour/nuit | `GET /api/v1/stats/jour-nuit` | donut 2 parts (jour = ambre, nuit = indigo) |
| V1.4 Top opérateurs | `GET /api/v1/stats/operateurs?limit=5` | barres horizontales triées |
| V1.3 Densité des départs | `GET /api/v1/stats/departs` | carte géo, couleur/taille ∝ volume de départs |

**Performances** : ces endpoints lisent des **vues matérialisées** (`mv_overview_kpi`,
`mv_operateurs`, `mv_departs`, cf. `etl/views.py`) - les agrégats sur ~13M trajets sont
**précalculés** et rafraîchis par l'ETL (`REFRESH MATERIALIZED VIEW CONCURRENTLY`, non bloquant
grâce à un **index unique** par vue). Un index B-tree classique n'aiderait pas une agrégation
plein-table.

Documentation interactive de l'API : **Swagger** sur `http://localhost:8000/docs`.

## Onglet « Explorateur de trajets » (V2)

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V2.1 Carte des liaisons | `GET /api/v1/trajets/liaisons?limit=N` | arcs O-D (train), regroupés jour/nuit, survol départ→arrivée |
| V2.2 Table des trajets | `GET /api/v1/trajets` (filtres, `sort`, `page`, `page_size`) | table paginée / triée / filtrée **côté serveur** |
| V2.3 Histogramme des distances | `GET /api/v1/trajets/distances?bin_km=100` | barres empilées jour/nuit |
| V2.4 Détail d'un trajet | `GET /api/v1/trajets/{id}` | panneau details-on-demand (clic sur une ligne) |

**Vues & index** : la **carte** (`mv_liaisons`) et l'**histogramme** (`mv_distance_hist`) lisent
des vues matérialisées (agrégats *train-only* précalculés, index unique pour le refresh concurrent).
La **table** et le **détail** manipulent de la donnée ligne à ligne : ils s'appuient sur les **index
existants** de `trajets` (filtres) et la **clé primaire** (détail) — pas de vue ni d'index superflu.

## Onglet « Empreinte carbone » (V5)

Question centrale : **le train, alternative crédible à l'avion ?**

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V5.1 CO₂ évité vs avion | `GET /api/v1/stats/co2/comparaison-avion?facteur_avion_g_par_pkm=N` | compteur (callout CO₂ évité) + barres comparées train réel vs estimation avion par tranche de distance |
| V5.2 Distance × intensité | `GET /api/v1/stats/co2/scatter` | nuage de densité (distance × CO₂/pkm), bulles ∝ volume, couleur par mode |
| V5.3 Distribution par mode | `GET /api/v1/stats/co2/par-mode` | box plot du CO₂/pkm, train vs avion |

**Méthodo (transparence)** : le **facteur avion** (gCO₂e / voyageur-km) est un paramètre **exogène,
documenté et affiché** (défaut `230 g/pkm`, ordre de grandeur ADEME/EEA pour le court/moyen-courrier),
surchargeable par requête. L'estimation avion applique ce facteur aux **voyageur-km** parcourus en train.

**Vues & index** : les trois endpoints lisent des **vues matérialisées** (`mv_co2_comparaison`,
`mv_carbon_density`, `mv_co2_distribution`) — agrégats train/avion (totaux par tranche, histogramme 2D,
quartiles) **précalculés** sur ~13M trajets, chacune dotée d'un **index unique** pour le refresh concurrent.
Le front ne reçoit que des agrégats, jamais les points bruts.

## Qualité & workflow

- **CI** : GitHub Actions (`.github/workflows/ci.yml`) - lint, tests, build des images Docker.
- **Lint/format** : `ruff` (config par service). **Hooks** : `pre-commit` (`.pre-commit-config.yaml`).
- **Branches** : GitHub Flow - `feat/…`, `fix/…` → PR → CI verte → revue → merge sur `main`.
- **Commits** : [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `ci:`, `docs:`…).
- **Secrets** : `.env` local (gitignored), GitHub Secrets en CI. Jamais de secret commité.

## Feuille de route

**Réalisé** : socle conteneurisé, schéma + ETL (ingestion & résolution des jointures),
**onglet Vue d'ensemble** (KPI, jour/nuit, opérateurs, départs), **onglet Explorateur de
trajets** (liaisons, table, histogramme, détail) et **onglet Empreinte carbone**
(CO₂ évité vs avion, densité distance × intensité, distribution par mode).

**À venir** :

- **Onglets** : Jour/Nuit (détaillé), Opérateurs,
  Territoires & couverture, Fragilité/Clusters, Qualité des données, Supervision.
- **Monitoring** : Prometheus + Grafana. **Tests E2E** : Playwright.
