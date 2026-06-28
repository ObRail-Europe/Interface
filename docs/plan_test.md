# Plan de Test — ObRail Europe (MSPR TPRE532)

> Document de référence pour la **stratégie de test** de la plateforme ObRail Europe. Il définit **ce qui est
> testé** (périmètre, niveaux, types), **comment** (environnements, outils, automatisation CI) et **selon quels
> critères** le logiciel est considéré comme prêt à être livré (entrée/sortie, anomalies, acceptation).

---

## 1. Identification du document

| Champ | Valeur |
| --- | --- |
| Projet | ObRail Europe — observatoire du ferroviaire et de la mobilité bas-carbone |
| Module de formation | MSPR TPRE532 |
| Document | Plan de test |
| Version | 1.0 |
| Date | 2026-06-28 |
| Statut | En vigueur |
| Dépôt | `ObRail-Europe/Interface` |
| Périmètre couvert | `database/`, `api/`, `dashboard/`, CI/CD, monitoring |

### Historique des versions

| Version | Date | Auteur | Description |
| --- | --- | --- | --- |
| 1.0 | 2026-06-28 | Lohan LACROIX | Création initiale, alignée sur l'état du dépôt à la phase d'industrialisation |

---

## 2. Introduction

### 2.1 Contexte

ObRail Europe est une plateforme conteneurisée composée de trois projets Python indépendants
(`database`, `api`, `dashboard`) exposant ~13 millions de trajets ferroviaires, ~10 000 communes
françaises et un modèle de clustering de fragilité territoriale, via une API REST FastAPI et un
dashboard Dash/Plotly à 9 onglets. Le dépôt correspond à la **phase d'industrialisation** du
prototype : conteneurisation complète, pipeline CI/CD, gate de couverture de tests et stack de
supervision (Prometheus/Loki/Grafana).

### 2.2 Objectifs du plan de test

- Définir le **périmètre** des activités de test (ce qui est couvert, ce qui ne l'est pas et pourquoi).
- Décrire la **stratégie** : niveaux de test (unitaire, intégration, système), types de test
  (fonctionnel, données, ML, performance, sécurité, accessibilité, observabilité) et leur répartition
  entre les trois modules.
- Fixer les **critères d'entrée et de sortie** qui conditionnent une mise en production.
- Cartographier la **couverture fonctionnelle** existante (39 fichiers de test) au regard des 9 onglets
  et des 27+ endpoints du dashboard.
- Décrire le **processus de gestion des anomalies** et les **outils** d'automatisation (pytest, ruff,
  pre-commit, GitHub Actions).
- Identifier les **risques** propres au domaine (volumétrie, qualité des jointures, dérive du modèle ML)
  et leurs mitigations.

### 2.3 Public visé

Équipe de développement ObRail Europe, relecteurs de pull request, jury/coach MSPR, et toute personne
reprenant le projet et souhaitant comprendre comment la qualité logicielle est garantie.

---

## 3. Documents de référence

| Document | Contenu |
| --- | --- |
| [`README.md`](../README.md) | Architecture générale, démarrage, structure, qualité & workflow |
| [`docs/conception-visualisations.md`](conception-visualisations.md) | Spécification des 9 onglets, contrats d'API, DTO, règles RGAA |
| [`api/README.md`](../api/README.md) | Architecture en couches de l'API, endpoints, stratégie de test du service |
| [`database/README.md`](../database/README.md) | Modèles, migrations, ETL, fixtures et plugin pytest partagé |
| [`dashboard/README.md`](../dashboard/README.md) | Composants purs, clients HTTP, stratégie de test du frontend |
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Pipeline d'intégration continue (lint, tests, build) |
| [`.github/workflows/cd.yml`](../.github/workflows/cd.yml) | Pipeline de publication des images sur GHCR |
| [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Hooks exécutés avant commit (lint, secrets, fichiers volumineux) |

---

## 4. Périmètre des tests

### 4.1 Dans le périmètre

- **Tests unitaires et d'intégration automatisés** des trois modules (`database`, `api`, `dashboard`),
  exécutés en local (`uv run pytest`) et en CI à chaque push/PR.
- **Couverture fonctionnelle** des 27+ endpoints REST (`/api/v1/...`) et de leurs DTO, des composants
  d'affichage purs du dashboard et des clients HTTP qui les alimentent.
- **Tests du modèle de Machine Learning** de fragilité (inférence, reproduction de partition).
- **Tests de qualité des données** (complétude, anomalies, volumétrie) exposés comme fonctionnalité
  métier (onglet « Qualité des données »).
- **Tests d'infrastructure applicative** : healthchecks, format des logs structurés, gestion d'erreurs
  normalisée, exposition des métriques Prometheus.
- **Lint et formatage** (ruff) comme porte de qualité de code, intégrée à la CI.
- **Build Docker** des trois images (validation de constructibilité, sans déploiement) sur chaque PR.
- **Tests manuels exploratoires** du dashboard (parcours utilisateur, accessibilité) avant chaque mise
  en production, en complément de l'automatisation.

### 4.2 Hors périmètre (et justification)

| Hors périmètre | Justification / statut |
| --- | --- |
| Tests end-to-end automatisés (navigateur) | Aucun framework E2E n'est encore intégré ; inscrit en feuille de route (« À venir : Tests E2E Playwright », cf. [`README.md`](../README.md)). Couvert pour l'instant par des tests manuels (§9). |
| Tests de charge / performance à grande échelle | Aucun outil de charge (k6, Locust...) n'est en place. Les vues matérialisées limitent le besoin immédiat (agrégats précalculés sur ~13M lignes), mais hors périmètre MSPR. |
| Audit de sécurité formel (pentest) | Hors cadre MSPR ; seule la détection de secrets (`gitleaks`) est automatisée. |
| Tests de migration de données en production | L'ETL est testé en intégration sur jeux de données *seed* ; un rejeu complet sur les ~13M trajets réels n'est pas exécuté en CI (coût/temps). |
| Tests multi-navigateurs / responsive automatisés | Le dashboard est testé comme fonctions pures (sans rendu navigateur) ; le rendu visuel réel est vérifié manuellement (§9). |
| Tests de l'infrastructure monitoring elle-même (Prometheus/Loki/Grafana) | Composants tiers, configurés par provisioning ; vérifiés manuellement à la mise en place, pas en CI. |

---

## 5. Stratégie de test

### 5.1 Niveaux de test

| Niveau | Description | Outil | Responsable |
| --- | --- | --- | --- |
| **Unitaire** | Logique métier isolée : modèles ORM, services (doublures en mémoire), composants Dash comme fonctions pures `données → figure` | `pytest` | Auteur de la fonctionnalité |
| **Intégration** | Composant + ses dépendances directes : endpoints API sur base *seed* (`TestClient`), ETL contre PostgreSQL réel, requêtes SQL des vues matérialisées | `pytest` + PostgreSQL 16 (service CI ou local) | Auteur de la fonctionnalité, revu en PR |
| **Système (manuel)** | Stack complète assemblée (`docker compose up`) : chaîne `migrate → load → api → dashboard`, navigation des 9 onglets, supervision | Checklist manuelle (§9) | Avant chaque mise en production |
| **Non-régression** | Rejeu de la suite complète à chaque push/PR, gate de couverture 70 % | GitHub Actions CI | Automatique |
| **Coverage**    | La suite de test échoue pour un coverage inférieur à 70% | Ce taux s'explique par la présence de composant visuel dans le dashboard complexe à tester et de fonction SQL volumineuse en proportion |

### 5.2 Types de test

| Type | Où | Exemple concret |
| --- | --- | --- |
| **Fonctionnel** | Tous modules | `GET /api/v1/trajets` retourne une page triée/filtrée conforme au DTO `Page<TrajetDTO>` |
| **Données / qualité** | `api/tests/test_qualite_*`, `database/tests/test_etl_*` | Complétude par colonne, détection de doublons `trip_id`, résolution des jointures villes/clusters |
| **Modèle ML** | `api/tests/test_fragilite_model.py` | Reproduction de la partition KMeans d'origine, inférence numpy pure sans scikit-learn |
| **Performance ciblée** | Vues matérialisées (`mv_*`) | Lecture d'agrégats précalculés plutôt que scan des ~13M trajets (validé par construction, pas par chrono CI) |
| **Sécurité (basique)** | Pre-commit | `gitleaks` (détection de secrets), `check-added-large-files` (anti-commit de jeux de données) |
| **Accessibilité (RGAA)** | Manuel (§9) | Contraste AA, équivalent textuel des graphiques, navigation clavier — voir `docs/conception-visualisations.md` §3 |
| **Observabilité** | `api/tests/test_logging.py`, `test_error_handling.py`, `test_supervision_api.py` | Format JSON structuré des logs, `ApiError` normalisée, `/health/details` |
| **Infrastructure (build)** | CI (`build-test`) | Build Docker dry-run des 3 images sur chaque PR |

### 5.3 Approche par module

| Module | Niveau dominant | Particularités | Dépendances de test |
| --- | --- | --- | --- |
| `database/` | Intégration | ORM, migrations Alembic, ETL (chargement Polars, résolution des jointures), vues matérialisées | PostgreSQL 16 dédié, fixtures CSV/Parquet d'échantillon |
| `api/` | Unitaire (services) + Intégration (endpoints) | Doublures en mémoire pour les services, base *seed* pour les endpoints, modèle ML réel | PostgreSQL 16 dédié, `.joblib` réels, plugin pytest partagé avec `database` |
| `dashboard/` | Unitaire | Composants comme fonctions pures (assertions sur la structure Plotly, pas de rendu) ; clients HTTP testés via doublure de transport | Aucune (ni API ni navigateur requis) |

---

## 6. Environnements et données de test

### 6.1 Environnements

| Environnement | Usage | Caractéristiques |
| --- | --- | --- |
| **Local développeur** | Développement et exécution ciblée des tests | `uv sync && uv run pytest` par module ; PostgreSQL local ou conteneur pour `database`/`api` |
| **CI (GitHub Actions)** | Exécution systématique à chaque push/PR | Jobs parallèles par service, conteneur `postgres:16` éphémère (service container), checkout avec `lfs: true` pour `database`/`api` ; échouent si le coverage par module < 70% |
| **Stack complète (Docker Compose)** | Tests système manuels, recette avant mise en production | `docker compose up --build` : `db` → `migrate` → `load` → `api`/`dashboard` + monitoring |

### 6.2 Données de test

- **Jeux de données *seed*** : embarqués dans `database/src/obrail_database/fixtures/`
  (`villes_sample.csv`, `clusters_sample.csv`, `trajets_sample.parquet`,
  `trajets_flights_sample.parquet` pour les comparaisons carbone) — volumes réduits, déterministes,
  couvrant les cas représentatifs (trajets jour/nuit, communes avec/sans gare, etc.).
- **Base de test dédiée** : `TEST_DATABASE_URL` (ou base configurée suffixée `_test`, créée
  automatiquement si absente), isolée des données de développement. Le plugin pytest partagé
  (`obrail_database.testing`) charge le jeu *seed*, résout les jointures et rafraîchit les vues
  matérialisées avant chaque session de test.
- **Comportement en l'absence de PostgreSQL** : les tests d'intégration sont **ignorés** (`pytest.skip`)
  plutôt qu'en échec ; les tests de métadonnées (modèles, schémas) tournent sans base. En CI, un
  service `postgres:16` est toujours disponible (`pg_isready` en *healthcheck*), donc les tests
  d'intégration s'exécutent réellement à chaque run.
- **Modèles ML** : les `.joblib` réels (`cluster_fragilite.joblib`, `preprocessing.joblib`) sont
  utilisés tels quels en test — pas de mock du modèle, pour garantir la non-régression de l'inférence.

### 6.3 Git LFS dans les tests

Le fichier `routes_france.parquet` (~630 Mo) est suivi par **Git LFS** (`*.parquet` dans
`.gitattributes`). Les jobs CI `test-database` et `test-api` effectuent un `checkout` avec `lfs: true`
afin de disposer des données réelles nécessaires aux migrations Docker (la suite pytest, elle, ne
consomme que les fixtures *seed* légères, indépendantes du Parquet versionné).

---

## 7. Critères d'entrée et de sortie

### 7.1 Critères d'entrée (avant d'exécuter une campagne de test)

- Le code à tester compile/s'importe sans erreur (`uv sync` réussi).
- Les migrations Alembic de la base de test sont applicables sans erreur (`Base.metadata.create_all`
  idempotent).
- L'environnement dispose d'un PostgreSQL 16 accessible (local, conteneur ou service CI).
- Les fixtures *seed* du module `database` sont présentes et chargées sans erreur.

### 7.2 Critères de sortie (gate de qualité avant fusion sur `main`)

| Critère | Seuil / condition | Vérifié par |
| --- | --- | --- |
| Lint | `ruff check` et `ruff format --check` sans erreur, par service | Job `lint` (matrice `database`/`api`/`dashboard`) |
| Tests unitaires & intégration | 100 % des tests passants, par service | Jobs `test-database`, `test-api`, `test-dashboard` |
| Couverture de code | **≥ 70 %** par service (`--cov-fail-under=70`) | `pytest-cov`, configuré dans chaque `pyproject.toml` |
| Constructibilité Docker | Build dry-run réussi des 3 images | Job `build-test` (déclenché sur PR uniquement) |
| Secrets | Aucun secret détecté dans les fichiers indexés | Hook `gitleaks` (pre-commit) |
| Revue de code | Pull request approuvée par un relecteur | Processus GitHub (GitHub Flow) |

> Une pull request ne peut être fusionnée sur `main` que si l'ensemble de ces critères est vert — la CI
> matérialise ce gate (`concurrency` annule les runs obsolètes de la même branche/PR).

---

## 8. Couverture fonctionnelle des tests

### 8.1 Module `database/` (7 fichiers de test)

| Fichier | Objet testé | Type |
| --- | --- | --- |
| `test_trajet_model.py` | Modèle ORM `Trajet` (contraintes, types, clé technique `id`) | Unitaire |
| `test_ville_model.py` | Modèle ORM `Ville` (clé INSEE `citycode`, indicateurs socio-éco) | Unitaire |
| `test_cluster_model.py` | Modèle ORM `Cluster` (clé `row_id`, niveau de fragilité) | Unitaire |
| `test_etl_loaders.py` | Chargement CSV (villes, clusters) et Parquet (trajets) via Polars | Intégration |
| `test_etl_resolve.py` | Résolution des jointures (`clusters.citycode` par coordonnées, `trajets.*_citycode` par nom normalisé) | Intégration |
| `test_etl_seed.py` | Cohérence du jeu de données *seed* (chargement + résolution + rafraîchissement des vues) | Intégration |
| `test_views.py` | Vues matérialisées (agrégats SQL sur le jeu *seed*) | Intégration |

### 8.2 Module `api/` (18 fichiers de test)

| Domaine fonctionnel | Fichiers de test | Type |
| --- | --- | --- |
| Vue d'ensemble / KPI | `test_overview_service.py`, `test_stats_api.py` | Unitaire + Intégration |
| Explorateur de trajets | `test_explorer_service.py`, `test_trajets_api.py` | Unitaire + Intégration |
| Empreinte carbone | `test_carbon_service.py`, `test_carbon_api.py` | Unitaire + Intégration |
| Territoires & couverture | `test_territoire_service.py`, `test_territoires_api.py` | Unitaire + Intégration |
| Fragilité territoriale (incl. modèle ML) | `test_fragilite_service.py`, `test_fragilite_api.py`, `test_fragilite_model.py`, `test_predict_api.py` | Unitaire + Intégration + ML |
| Qualité des données | `test_qualite_service.py`, `test_qualite_api.py` | Unitaire + Intégration |
| Supervision | `test_supervision_api.py` | Intégration |
| Infrastructure transverse | `test_health.py`, `test_logging.py`, `test_error_handling.py` | Intégration |

### 8.3 Module `dashboard/` (14 fichiers de test)

| Domaine fonctionnel | Fichiers de test | Type |
| --- | --- | --- |
| Montage de l'application | `test_smoke.py` | Smoke |
| Composants graphiques génériques | `test_components_charts.py`, `test_components_kpi.py`, `test_components_tables.py` | Unitaire (fonctions pures) |
| Composants par onglet | `test_components_carbon.py`, `test_components_territoires.py`, `test_components_fragilite.py`, `test_components_qualite.py`, `test_components_supervision.py` | Unitaire (fonctions pures) |
| Clients HTTP par onglet | `test_explorer_client.py`, `test_cluster_client.py`, `test_territoire_client.py`, `test_qualite_client.py`, `test_supervision_client.py` | Unitaire (doublure de transport) |

### 8.4 Scénarios de test représentatifs

Sélection de scénarios couvrant le cas nominal, les cas limites et les cas d'erreur, illustrant la
profondeur de la suite existante :

| ID | Scénario | Entrée | Résultat attendu | Type |
| --- | --- | --- | --- | --- |
| ST-01 | Liste paginée des trajets | `GET /api/v1/trajets?page=1&page_size=20` | `Page<TrajetDTO>` cohérente (`items`, `total`, `pages`) | Nominal |
| ST-02 | Filtrage croisé des trajets | `GET /api/v1/trajets?mode=train&night=true&distance_min=500` | Sous-ensemble respectant tous les filtres combinés | Nominal |
| ST-03 | Détail d'un trajet inexistant | `GET /api/v1/trajets/{id}` avec `id` absent | `404` avec `ApiError` normalisée | Erreur |
| ST-04 | Comparaison carbone avec facteur avion personnalisé | `GET /api/v1/stats/co2/comparaison-avion?facteur_avion_g_par_pkm=200` | Recalcul de l'estimation avion avec le facteur fourni | Limite (paramètre exogène) |
| ST-05 | Simulateur de fragilité — entrée valide | `POST /api/v1/fragilite/predict` avec features complètes | Cluster et niveau de fragilité prédits, cohérents avec le modèle `.joblib` | Nominal (ML) |
| ST-06 | Simulateur de fragilité — modèle indisponible | `MODEL_DIR` sans fichiers `.joblib` | `503` propre (pas de crash) | Erreur |
| ST-07 | Couverture par maille | `GET /api/v1/stats/couverture?by=code_dept` | Barres triées, taux de communes avec gare cohérent avec les données *seed* | Nominal |
| ST-08 | Qualité — anomalies | `GET /api/v1/qualite/anomalies` | Anomalies classées par sévérité (`info`/`warn`/`error`) | Nominal |
| ST-09 | Supervision — base indisponible | `GET /api/v1/health/details` avec PostgreSQL down (simulé en test service) | Statut `DOWN` reporté sans exception non gérée | Erreur |
| ST-10 | Résolution de jointures avec homonymes | ETL sur jeu *seed* contenant des communes homonymes | Résolution par gare puis population, alias documentés (Paris/Lyon/Marseille) | Limite |
| ST-11 | Composant KPI — données vides | Fonction pure de composant avec liste vide | Rendu d'un état vide sans exception | Limite |
| ST-12 | Client HTTP — erreur réseau | Doublure de transport simulant un timeout/erreur HTTP | Exception/erreur propagée de façon prévisible au composant appelant | Erreur |

---

## 9. Tests manuels complémentaires (hors automatisation actuelle)

À exécuter avant toute mise en production, en complément de la suite automatisée :

- **Parcours utilisateur** sur les 9 onglets du dashboard (Vue d'ensemble, Explorateur, Carbone,
  Territoires, Fragilité, Qualité, Supervision — les onglets Jour/Nuit détaillé et Opérateurs sont en
  feuille de route) : navigation, filtres globaux, cross-filtering, drill-down sur le détail d'un trajet.
- **Accessibilité (RGAA)** : navigation clavier complète, contraste AA, bascule « voir le tableau de
  données » sur chaque visualisation, absence d'information transmise uniquement par la couleur ou le
  survol — voir le détail des règles dans `docs/conception-visualisations.md` §3.
- **Test système de bout en bout** via `docker compose up --build` : vérifier la chaîne
  `db` (healthy) → `migrate` (schéma) → `load` (ingestion idempotente) → `api`/`dashboard` opérationnels,
  puis `docker compose --profile load run --rm force-load` pour la réingestion forcée.
- **Supervision** : badges de santé (`/health`, `/health/details`) à jour toutes les 10 s, métriques
  Prometheus exposées sur `/metrics`, dashboard Grafana « ObRail - Supervision » provisionné et
  affichant logs/métriques en quasi temps réel.
- **Cohérence visuelle des graphiques Plotly** rendus dans un navigateur réel (les tests automatisés ne
  vérifient que la structure des données, pas le rendu pixel).

> **Évolution prévue** : automatisation de ces parcours via **Playwright** (cf. feuille de route du
> [`README.md`](../README.md)) — ce plan de test sera mis à jour en conséquence à l'intégration de l'outil.

---

## 10. Gestion des anomalies

- **Outil de suivi** : GitHub Issues du dépôt `ObRail-Europe/Interface`.
- **Cycle de vie** : Ouverte → Qualifiée (sévérité assignée) → En cours (branche `fix/...`) → Corrigée
  (PR) → CI verte → Revue → Fermée (merge sur `main`).
- **Classification de sévérité** :

| Sévérité | Définition | Exemple dans le contexte ObRail |
| --- | --- | --- |
| Bloquante | Empêche le démarrage de la stack ou rend un service indisponible | `docker compose up` échoue, `/health` ne répond jamais |
| Majeure | Fonctionnalité métier incorrecte sans contournement simple | Le simulateur de fragilité renvoie un cluster erroné |
| Mineure | Comportement incorrect avec contournement possible, n'affecte pas la donnée | Tri par défaut incorrect sur la table des trajets |
| Cosmétique | Écart visuel ou de libellé sans impact fonctionnel | Couleur jour/nuit incohérente sur un graphique secondaire |

- **Règle de non-régression** : toute correction d'anomalie s'accompagne d'un test (unitaire ou
  d'intégration) qui aurait permis de la détecter, ajouté à la suite pytest concernée avant fusion.
- **Anomalies bloquantes ou majeures** : interdiction de fusion sur `main` tant qu'elles sont ouvertes
  sur le périmètre concerné par la pull request.

---

## 11. Outils et intégration continue

| Outil | Rôle |
| --- | --- |
| `pytest` (≥ 9.1) | Exécution des suites de test des trois modules |
| `pytest-cov` (≥ 7.1) | Mesure de couverture, gate `--cov-fail-under=70` |
| `ruff` (≥ 0.15) | Lint (`check`) et formatage (`format --check`) Python |
| `pre-commit` | Exécution locale des hooks avant commit (whitespace, YAML/TOML, fichiers volumineux, secrets, ruff) |
| `gitleaks` | Détection de secrets dans les modifications indexées |
| `uv` | Gestion des dépendances et environnements virtuels par service, exécution reproductible (`uv sync --frozen`) |
| `Git LFS` | Versioning du fichier `routes_france.parquet` (~630 Mo), récupéré en CI (`lfs: true`) |
| `GitHub Actions` (CI) | Pipeline `lint` → `test-database`/`test-api`/`test-dashboard` (parallèles) → `build-test` (sur PR) |
| `GitHub Actions` (CD) | Build & publication des images sur GHCR (`main` → `latest` + SHA, tags semver → version exacte) |
| `Docker Buildx` | Build multi-plateforme (`linux/amd64`, `linux/arm64`) avec cache GitHub Actions |

### Pipeline CI (`ci.yml`) — vue d'ensemble

```
push / pull_request
   │
   ├─▶ lint (matrice database · api · dashboard)         — ruff check + format --check
   ├─▶ test-database (+ service postgres:16)             — uv run pytest, lfs: true
   ├─▶ test-api (+ service postgres:16)                  — uv run pytest, lfs: true
   ├─▶ test-dashboard                                     — uv run pytest (sans base)
   │
   └─▶ build-test (uniquement si pull_request, dépend des 4 jobs précédents)
          ├─ build image database (dry-run)
          ├─ build image api (dry-run)
          └─ build image dashboard (dry-run)
```

La concurrence (`concurrency: cancel-in-progress`) annule automatiquement les exécutions précédentes
d'une même branche/PR encore en cours, pour ne conserver que le résultat le plus récent.

---

## 12. Rôles et responsabilités

Le projet est porté par l'équipe **ObRail Europe** dans le cadre du module MSPR.

| Rôle | Responsabilité |
| --- | --- |
| Auteur de la fonctionnalité | Écrit les tests unitaires/intégration couvrant le code produit, avant ou avec le développement |
| Relecteur de pull request | Vérifie la pertinence des tests ajoutés et la couverture des cas limites/erreurs lors de la revue |
| CI (GitHub Actions) | Gardien automatique : exécute systématiquement lint, tests, gate de couverture et build à chaque push/PR |
| Mainteneur (pilotage qualité) | Maintient la configuration de test (fixtures partagées, seuil de couverture, pipeline CI/CD), arbitre les exceptions |

---

## 13. Planning et jalons

La feuille de route fonctionnelle du [`README.md`](../README.md) sert de référence pour le planning de
test : chaque fonctionnalité livrée est accompagnée de sa suite de tests avant fusion sur `main`.

| Statut | Périmètre | Couverture de test |
| --- | --- | --- |
| ✅ Réalisé | Socle conteneurisé, schéma + ETL | `database/tests/` (7 fichiers) |
| ✅ Réalisé | Onglets Vue d'ensemble, Explorateur, Carbone, Territoires, Fragilité (+ simulateur ML), Qualité, Supervision | `api/tests/` (18 fichiers) + `dashboard/tests/` (14 fichiers) |
| ✅ Réalisé | Monitoring (Prometheus/Loki/Grafana), logs structurés | `test_logging.py`, `test_error_handling.py`, `test_supervision_api.py` + vérification manuelle (§9) |
| ⏳ À venir | Onglets Jour/Nuit (détaillé), Opérateurs | Tests à concevoir au moment de l'implémentation, en suivant le même schéma (service + endpoint + composant + client) |
| ⏳ À venir | Tests E2E automatisés (Playwright) | Remplaceront progressivement les parcours manuels du §9 |

---

## 14. Risques liés aux tests et mitigations

| Risque | Impact | Probabilité | Mitigation |
| --- | --- | --- | --- |
| Indisponibilité de PostgreSQL en environnement local | Tests d'intégration silencieusement ignorés (`pytest.skip`), faux sentiment de couverture | Moyenne (local), faible (CI, service garanti) | Toujours valider la couverture réelle via la CI (service `postgres:16` garanti par `pg_isready`) avant de considérer une fonctionnalité validée |
| Volumétrie du Parquet (~630 Mo, Git LFS) | Ralentissement du checkout CI, quota LFS | Faible | `lfs: true` ciblé uniquement sur les jobs qui en ont besoin (`test-database`, `test-api`, `build-test`) ; la suite pytest elle-même n'en dépend pas (fixtures *seed* légères) |
| Résolution incomplète des jointures villes/trajets (~50 % non résolus pour l'étranger/quartiers) | Biais potentiel dans les agrégats si mal interprété | Connue et documentée | Comportement assumé et documenté (`README.md`) ; couvert par `test_etl_resolve.py` sur les cas d'homonymie résolus, à surveiller via l'onglet Qualité des données en production |
| Dérive du modèle de clustering si ré-entraîné (`cluster_fragilite.joblib`) | Le simulateur de fragilité produirait des résultats incohérents avec les données historiques | Faible (modèle figé) mais à surveiller en cas de ré-entraînement | `test_fragilite_model.py` vérifie la reproduction de la partition d'origine (~99,98 %) ; à exécuter systématiquement après tout remplacement des `.joblib` |
| Absence de test de charge sur les vues matérialisées | Risque de dégradation de performance en production non détecté avant mise en service | Moyenne | Test de charge formel (k6/Locust) à planifier comme évolution du périmètre (§4.2) |
| Absence de tests E2E automatisés | Régressions visuelles ou de parcours utilisateur non détectées avant mise en production | Moyenne | Tests manuels systématiques avant mise en production (§9) ; automatisation Playwright en feuille de route |

---

## 15. Critères d'acceptation et livrables

- **CI entièrement verte** (lint + tests + gate de couverture 70 % + build dry-run) sur la pull request,
  condition nécessaire à la fusion sur `main`.
- **Rapport de couverture** `pytest-cov` (`--cov-report=term-missing`) consulté en CI pour identifier les
  lignes non couvertes avant fusion.
- **Revue de code approuvée**, incluant la pertinence des tests ajoutés/modifiés.
- **Checklist manuelle (§9)** complétée avant toute mise en production (déploiement sur `main` /
  publication d'image taguée).
- **Aucune anomalie bloquante ou majeure ouverte** sur le périmètre livré (§10).

---

## 16. Annexes

### 16.1 Glossaire

| Terme | Définition |
| --- | --- |
| DTO | *Data Transfer Object* — schéma Pydantic définissant le contrat de réponse d'un endpoint |
| ETL | *Extract, Transform, Load* — pipeline d'ingestion des CSV/Parquet vers PostgreSQL |
| Gate (de qualité) | Condition automatique bloquant la fusion/le déploiement si elle n'est pas satisfaite |
| LFS | *Git Large File Storage* — extension Git pour versionner de gros fichiers binaires (ici, le Parquet) |
| RGAA | Référentiel Général d'Amélioration de l'Accessibilité (norme française d'accessibilité numérique) |
| Vue matérialisée | Vue SQL dont le résultat est précalculé et stocké, rafraîchie explicitement (ici via l'ETL) |
| Doublure (test double) | Implémentation simplifiée d'une dépendance (en mémoire) substituée en test pour isoler le code testé |

### 16.2 Suivi des révisions

Ce document doit être mis à jour à chaque évolution significative du périmètre testé (nouvel onglet,
nouveau type de test, changement de seuil de couverture, intégration de Playwright) — voir le tableau
de version en §1.
