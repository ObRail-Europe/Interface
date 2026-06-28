# dashboard — frontend Dash/Plotly ObRail

Interface de consultation et de visualisation (Dash / Plotly). Destinée à un public **non technique
mais exigeant** (institutions, ONG, opérateurs) ; consomme l'API REST et embarque des panneaux Grafana
pour la supervision. Projet uv indépendant, servi par gunicorn.

## Onglets (9)

Vue d'ensemble · Explorateur de trajets · Empreinte carbone · Territoires & couverture ·
Fragilité territoriale (+ **simulateur** du modèle) · Qualité des données · Supervision (santé +
Grafana embarqué). Un onglet ouvre sur une synthèse puis le filtrage/drill-down (Shneiderman).

## Architecture en couches

| Couche | Dossier | Rôle |
| --- | --- | --- |
| Infrastructure | `api/` | clients de l'API : `Protocol` + implémentation HTTP (`BaseHttpClient`) |
| Présentation | `components/` | fonctions **pures** `données → figure/composant` (testables sans navigateur) |
| Page | `pages/` | layout + callbacks d'un onglet ; le client est **injecté** |
| Thème | `theme.py`, `assets/theme.css` | tokens couleurs data-viz (jour/nuit, carbone, fragilité…) |

`main.py` (`create_app()`) injecte un client HTTP par onglet, assemble les `dcc.Tab` et câble les
callbacks. `server = app.server` est exposé pour gunicorn.

## Principes data-viz

- **Une question = une visualisation**, titrée comme telle ; encodages sémantiques constants
  (jour = ambre, nuit = indigo) ; barres à axe zéro ; sobriété (pas de 3D).
- **Performance** : toutes les agrégations sont faites côté API ; le front ne reçoit que de l'agrégé
  ou du paginé (jamais les ~13M lignes brutes).
- **Accessibilité (RGAA)** : pas d'information par la seule couleur, libellés directs, formulaires
  étiquetés (simulateur), région ARIA live pour les résultats.

## Configuration (env)

`API_URL` (base de l'API, défaut `http://api:8000`) · `GRAFANA_URL` (panneaux embarqués V9).

## Développement

```bash
uv sync
uv run python main.py     # dashboard local sur :8050 (API requise, cf. API_URL)
uv run pytest -q          # tests (composants purs + clients, sans navigateur ni API)
uv run ruff check && uv run ruff format
```

**Tests** : les `components/` sont testés comme **fonctions pures** (figures Plotly assertées sans
rendu) ; les clients `api/` via une doublure du transport HTTP (chemins/paramètres construits) ;
un test smoke vérifie le montage de l'app.

## Conteneurisation

`dashboard/Dockerfile` (contexte `./dashboard`) ; image servie par **gunicorn** (`main:server`).
Dans la stack, le service `dashboard` dépend de `api`.
