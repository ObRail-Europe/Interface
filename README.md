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

| Service      | Stack                       | Port  | Rôle                                            |
| ------------ | --------------------------- | ----- | ----------------------------------------------- |
| `db`         | PostgreSQL 16               | 5432  | Persistance des données (volume `pgdata`)       |
| `api`        | FastAPI + SQLAlchemy (uv)   | 8000  | API REST, doc OpenAPI/Swagger sur `/docs`       |
| `dashboard`  | Dash / Plotly (uv)          | 8050  | Interface de consultation et de visualisation   |
| `prometheus` | Prometheus                  | 9090  | Collecte des métriques de l'API (`/metrics`)    |
| `loki`       | Grafana Loki                | 3100  | Agrégation des logs applicatifs                 |
| `promtail`   | Grafana Promtail            | -     | Expédition des logs des conteneurs vers Loki    |
| `grafana`    | Grafana                     | 3000  | Tableaux de bord de supervision (métriques+logs)|

## Démarrage rapide (une seule commande)

```bash
cp .env.example .env
docker compose up --build                          # db + schéma + données + api + dashboard + monitoring
docker compose --profile load run --rm force-load  # réingestion forcée des données (optionnel)
```

- API : http://localhost:8000/health · Swagger : http://localhost:8000/docs
- Dashboard : http://localhost:8050
- Supervision : http://localhost:3000 (Grafana, accès anonyme) · Prometheus : http://localhost:9090

> Au démarrage, le service `migrate` provisionne le **schéma** (tables + index + vues), puis `load`
> **ingère les données** (idempotent : ne recharge pas si la base contient déjà des données).
> Les deux s'appuient sur l'image auto-portante `obrail-database` (cf. § Base de données).

## Développement local (par service)

Trois projets Python 3.13 indépendants gérés par [`uv`](https://docs.astral.sh/uv/) :
`database/` (couche base), `api/` (backend, dépend de `database`), `dashboard/` (frontend).

```bash
cd api          # ou: cd database, cd dashboard
uv sync               # installe les dépendances (crée .venv + uv.lock)
uv run pytest         # tests (intégration : PostgreSQL requis, cf. § Base de données)
uv run ruff check     # lint
uv run ruff format    # formatage
uv run uvicorn main:app --reload      # API en local (port 8000)
# uv run python main.py                # Dashboard en local (port 8050)
```

## Base de données - module `database/`

Toute la **gestion de PostgreSQL** (modèles ORM, migrations Alembic, vues matérialisées, ETL
d'ingestion des CSV) vit dans un **projet uv indépendant** `database/` (package `obrail_database`),
distinct de l'API qui n'en consomme que les **modèles** via une dépendance path éditable
(`from obrail_database.models import …`). Le module embarque sa propre **image Docker**
(`obrail-database`) : tirée et lancée, elle provisionne le schéma (tables + index + vues) et embarque
les CSV pour le chargement - **auto-portante**, sans dépendre du dépôt.

Trois tables, alimentées par les CSV de `data/` (modèles SQLAlchemy 2.0 dans
`database/src/obrail_database/models/`) :

| Table | Source (`data/`) | Clé primaire | Contenu |
| --- | --- | --- | --- |
| `villes` | `villes_enriched.csv` (~10k) | `citycode` (INSEE) | desserte + indicateurs socio-éco par commune |
| `clusters` | `clusters_final.csv` (~10k) | `row_id` | cluster de fragilité + features (modèle `cluster_fragilite.joblib`) |
| `trajets` | `routes_france.csv` (~13M) | `id` (surrogate) | trajets ferroviaires : horaires, géo, calendrier, CO₂ |

**Schéma** : géré par Alembic, appliqué automatiquement dans la stack (service `migrate`). En local :

```bash
cd database
uv run alembic upgrade head                       # tables + index + vues matérialisées
# uv run python -m obrail_database.init_db          # alternative create_all (prototypage)
```

**Données** : ingestion des CSV + résolution des jointures (idempotente : saute si la base contient
déjà des données).

```bash
docker compose up                                        # le service `load` ingère au 1er démarrage
docker compose --profile load run --rm force-load        # réingestion forcée (--force)
cd database && uv run python -m obrail_database.etl.run  # en local (base lancée, CSV dans data/)
#   options : --trajets-limit N · --skip-trajets · --skip-resolve · --force
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
├── docker-compose.yml      # db + migrate/load + api + dashboard + monitoring
├── .env.example            # variables d'environnement (modèle)
├── database/               # couche base : projet uv indépendant, image `obrail-database`
│   ├── Dockerfile          # image qui provisionne le schéma (et embarque les CSV)
│   ├── alembic.ini
│   ├── src/obrail_database/
│   │   ├── models/         # modèles ORM : Base, Ville, Cluster, Trajet
│   │   ├── migrations/     # Alembic (création des vues matérialisées incluse)
│   │   ├── etl/            # ingestion CSV + résolution des jointures + vues
│   │   ├── config.py · engine.py · logging_config.py · testing.py  # plugin pytest partagé
│   │   └── fixtures/       # CSV seed (tests)
│   └── tests/              # tests modèles / ETL / vues
├── api/                    # backend FastAPI (dépend de obrail-database pour les modèles)
│   ├── main.py             # create_app() : routers + GET /health
│   ├── routers/ services/ repositories/ schemas/ ml/   # accès REST en couches
│   ├── dependencies.py · database.py                    # injection + session SQLAlchemy
│   └── tests/              # tests endpoints / services
├── dashboard/              # frontend Dash (couches api/components/pages)
│   ├── main.py             # create_app() : onglets + server (gunicorn)
│   ├── api/ components/ pages/
│   └── tests/
├── data/                   # CSV (gitignorés) + modèles .joblib
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
existants** de `trajets` (filtres) et la **clé primaire** (détail) - pas de vue ni d'index superflu.

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
`mv_carbon_density`, `mv_co2_distribution`) - agrégats train/avion (totaux par tranche, histogramme 2D,
quartiles) **précalculés** sur ~13M trajets, chacune dotée d'un **index unique** pour le refresh concurrent.
Le front ne reçoit que des agrégats, jamais les points bruts.

## Onglet « Territoires & couverture ferroviaire » (V6)

Question centrale : **qui est bien / mal desservi ?**

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V6.1 Carte de la couverture | `GET /api/v1/villes/carte` (`dimension`, `code_dept`, `code_region`, `has_gare`) | carte des communes (couleur = dimension au choix, taille ∝ population) |
| V6.2 Couverture par maille | `GET /api/v1/stats/couverture?by=code_dept\|code_region` | barres triées par desserte, couleur = taux de communes avec gare |
| V6.4 Amplitude de service | `GET /api/v1/stats/amplitude?bin_h=1` | histogramme de l'amplitude moyenne + part desservie après minuit |

**Vues & index** : pas de vue matérialisée ici - la source est la table **`villes` (~10k communes)** avec des
métriques **déjà pré-calculées** (`nb_trajets_total`, `amplitude_moy_h`, `accessibilite_ord`…) ; les lectures et
agrégations (par maille, histogramme) sont donc directes et triviales. Les colonnes filtrées (`code_dept`,
`code_region`, `has_gare`) sont **déjà indexées** au schéma - pas d'index superflu. (Une vue matérialisée se
justifie pour agréger les ~13M trajets, pas pour 10k communes.)

## Onglet « Fragilité territoriale » (V7)

Question centrale : **quels territoires sont fragiles ? (modèle de clustering)**

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V7.1 Carte des clusters | `GET /api/v1/clusters/carte` (`code_dept`, `code_region`, `has_gare`) | communes colorées par cluster (palette daltonisme-safe) |
| V7.4 Effectifs des clusters | `GET /api/v1/clusters` | barres horizontales des effectifs par cluster |
| V7.2 Profils des clusters | `GET /api/v1/clusters/profils` | coordonnées parallèles des features normalisées 0–1 |
| V7.3 Fragilité par maille | `GET /api/v1/stats/fragilite?by=code_region\|code_dept` | barres empilées par territoire, échelle de fragilité vert→rouge |
| V7.5 Simulateur (modèle live) | `POST /api/v1/fragilite/predict` | formulaire → cluster + niveau prédits |

**Vues & index** : comme l'onglet Territoires, la source est la table **`clusters` (~10k communes)**, déjà indexée
(`cluster`, `niveau_fragilite`, `citycode`) ; lectures/agrégations directes, **pas de vue matérialisée**.

**Modèle live (V7.5)** : le simulateur charge `cluster_fragilite.joblib` (KMeans **stratifié par `has_gare`**) +
`preprocessing.joblib` (imputation médiane, dérivation `dist_gare_corrected` / `stress_mobilite`, winsorisation IQR,
`log1p`), puis affecte au **centroïde le plus proche**. Inférence **numpy pure** (sans scikit-learn) ; reproduction
de la partition d'origine validée à **~99,98 %**. Les `.joblib` sont lus depuis `MODEL_DIR` (volume `./data` monté en
lecture seule ; `503` propre si absents).

## Onglet « Qualité des données » (V8)

Question centrale : **peut-on faire confiance aux données ?**

| Viz | Endpoint API | Visualisation |
| --- | --- | --- |
| V8.1 Complétude par colonne | `GET /api/v1/qualite/completude?table=trajets\|villes\|clusters` | barres horizontales du % de complétude (rouge → vert) |
| V8.2 Anomalies & doublons | `GET /api/v1/qualite/anomalies` | barres colorées par sévérité (info / warn / error) |
| V8.4 Volumétrie par source | `GET /api/v1/qualite/volumetrie` | barres du nombre de trajets par source |

**Vues & index** : ici les audits **scannent les ~13M trajets** (NULLs par colonne, doublons `trip_id`, volumétrie
par source) - une **vue matérialisée est donc justifiée** (à la différence des onglets Territoires/Fragilité sur 10k
lignes). Trois vues (`mv_qualite_completude`, `mv_qualite_anomalies`, `mv_qualite_volumetrie`), chacune avec un index
unique pour le refresh concurrent. La vue de complétude est **générée depuis les modèles ORM** (un seul scan par table
via dé-pivot `VALUES`).

## Onglet « Supervision » & observabilité (V9)

Question centrale : **le service est-il sain ?**

| Viz | Source | Visualisation |
| --- | --- | --- |
| V9.1 État de santé | `GET /health`, `GET /api/v1/health/details` | badges UP/DOWN (API, base) + latence, rafraîchis toutes les 10 s |
| V9.2 Métriques | `GET /metrics` (Prometheus) → Grafana | disponibilité, req/s, latence p50/p95, taux d'erreurs |
| V9.3 Journal applicatif | logs → Promtail → Loki → Grafana | flux des logs applicatifs en temps réel |

**Stack monitoring** (lancée par `docker compose up`) : l'API est instrumentée
(`prometheus-fastapi-instrumentator`) et expose `/metrics` ; **Prometheus** la scrape, **Promtail** ramasse les logs
des conteneurs vers **Loki**, et **Grafana** (provisionné : datasources + dashboard *ObRail - Supervision*) restitue
métriques et logs. L'onglet front embarque ce dashboard Grafana (mode kiosk) sous les badges de santé.

| Service | Port | Rôle |
| --- | --- | --- |
| `prometheus` | 9090 | collecte des métriques de l'API |
| `loki` | 3100 | agrégation des logs |
| `promtail` | - | expédition des logs des conteneurs vers Loki |
| `grafana` | 3000 | tableaux de bord (métriques + logs), accès anonyme + embedding |

**Politique de logs** : journalisation **structurée JSON** sur stdout (API + dashboard), niveau configurable
(`LOG_LEVEL`), middleware FastAPI journalisant chaque requête (latence, statut) et **gestion d'erreurs normalisée**
(`ApiError { detail, code }` + exceptions métier). Aucune écriture de fichier - les logs sont collectés depuis stdout.

**Vues & index** : aucune n'est nécessaire - la supervision repose sur des **sondes live** (`SELECT 1`),
l'**instrumentation** Prometheus et l'**agrégation de logs**, pas sur des agrégations de données métier.

## Qualité & workflow

- **CI** : GitHub Actions (`.github/workflows/ci.yml`) - lint, tests, build des images Docker.
- **Lint/format** : `ruff` (config par service). **Hooks** : `pre-commit` (`.pre-commit-config.yaml`).
- **Branches** : GitHub Flow - `feat/…`, `fix/…` → PR → CI verte → revue → merge sur `main`.
- **Commits** : [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `ci:`, `docs:`…).
- **Secrets** : `.env` local (gitignored), GitHub Secrets en CI. Jamais de secret commité.

## Feuille de route

**Réalisé** : socle conteneurisé, schéma + ETL (ingestion & résolution des jointures),
**onglet Vue d'ensemble** (KPI, jour/nuit, opérateurs, départs), **onglet Explorateur de
trajets** (liaisons, table, histogramme, détail), **onglet Empreinte carbone**
(CO₂ évité vs avion, densité distance × intensité, distribution par mode),
**onglet Territoires & couverture** (carte des communes, couverture par maille, amplitude de service),
**onglet Fragilité territoriale** (carte des clusters, effectifs, profils, répartition par maille,
simulateur live), **onglet Qualité des données** (complétude, anomalies, volumétrie) et
**onglet Supervision** (santé, métriques & journal via Prometheus / Loki / Grafana).

**Monitoring** : Prometheus + Loki + Promtail + Grafana, lancés avec la stack ; logs structurés JSON.

**À venir** :

- **Onglets** : Jour/Nuit (détaillé), Opérateurs.
- **Tests E2E** : Playwright.
