# obrail-database

Couche **base de données** d'ObRail Europe : modèles ORM, migrations Alembic, vues matérialisées et
ETL d'ingestion (CSV + Parquet). Projet uv **indépendant** (package `obrail_database`), consommé par
l'API (qui n'en importe que les modèles) et déployable seul via son image Docker publiée sur ghcr.io.

## Contenu

| Élément | Emplacement | Rôle |
| --- | --- | --- |
| Modèles ORM | `src/obrail_database/models/` | `Base`, `Ville`, `Cluster`, `Trajet` (schéma des 3 tables) |
| Migrations | `src/obrail_database/migrations/` | Alembic - crée tables, index **et vues matérialisées** |
| ETL | `src/obrail_database/etl/` | ingestion CSV/Parquet (`loaders`, lecture Polars), résolution des jointures (`resolve`), vues (`views`), CLI (`run`) |
| Fixtures de test | `src/obrail_database/fixtures/` | CSV seed embarqués |
| Plugin pytest | `src/obrail_database/testing.py` | fixtures `engine` / `seeded_session` / `carbon_session` partagées avec l'API |

## Usage

```bash
uv sync

# Schéma : tables + index + vues matérialisées (aucun CSV requis).
DATABASE_URL=postgresql+psycopg://obrail:obrail@localhost:5432/obrail uv run alembic upgrade head

# Ingestion (villes/clusters en CSV, trajets en Parquet ; idempotente, --force pour réécraser).
# routes_france.parquet est suivi par Git LFS : `git lfs pull` avant.
uv run python -m obrail_database.etl.run --data-dir ../data

uv run pytest        # tests (PostgreSQL requis)
uv run ruff check
```

## Image Docker

L'image `obrail-database` est **auto-portante** : elle provisionne le schéma et embarque les données
(CSV + Parquet). Construite depuis la **racine du dépôt** (elle copie `data/`) et **publiée sur
GitHub Container Registry** par la CD :

```bash
docker pull ghcr.io/<owner>/obrail-database               # image publiée (CD sur main)
# ou build local depuis la racine (nécessite `git lfs pull`) :
docker build -t obrail-database -f database/Dockerfile .
docker run --rm -e DATABASE_URL=… obrail-database         # CMD = alembic upgrade head (schéma)
docker run --rm -e DATABASE_URL=… obrail-database \
  python -m obrail_database.etl.run --data-dir /app/data  # chargement des données
```

Dans la stack, les services `migrate` (schéma) et `load` / `force-load` (données) utilisent cette image.

## Consommation par l'API

L'API déclare `obrail-database` en dépendance path éditable (`[tool.uv.sources]`) et importe les
modèles : `from obrail_database.models import Trajet`. La dépendance est **à sens unique**
(api → database) ; le module database ne connaît pas l'API.
