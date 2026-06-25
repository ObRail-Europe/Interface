# Conception du Dashboard ObRail — Visualisations, Onglets & Contrats d'API

> Document de conception (data-visualisation + contrats d'API) pour le frontend Dash/Plotly d'ObRail Europe.
> Il définit **quoi** afficher (catalogue de visualisations), **comment l'organiser** (onglets, UX/UI)
> et **avec quelles données** (endpoints + DTO).

---

## 1. Objectifs & besoin métier

ObRail Europe veut **mesurer le rôle des trains (jour et nuit) dans une mobilité durable** et leur potentiel comme
**alternative à l'avion** sur les trajets intra-européens (Green Deal, TEN-T). Le dashboard doit permettre à un public
**non technique mais exigeant** (institutions, ONG, opérateurs) de :

- **consulter et filtrer** les trajets ferroviaires ;
- lire des **indicateurs clés** : répartition jour/nuit, volumes par opérateur, empreinte carbone, couverture ;
- comprendre la **couverture territoriale** et la **fragilité** des territoires (modèle de clustering) ;
- visualiser l'**état de qualité des données** et la **santé du service** (supervision).

Trois jeux de données alimentent le dashboard (via PostgreSQL) :

| Source | Granularité | Contenu clé |
| --- | --- | --- |
| `trajets` (← `routes_france.csv`, ~13M) | 1 ligne = 1 trajet | mode, opérateur, ville/pays départ-arrivée, horaires, `is_night_train`, `distance_km`, `co2_per_pkm`, `emissions_co2`, `days_of_week` |
| `villes` (← `villes_enriched.csv`, ~10k) | 1 ligne = 1 commune | géo, population, densité, revenu, `taux_sans_voiture`, `part_65plus`, `nb_gares`, `has_gare`, `dist_gare_min_m`, amplitude de service |
| `clusters` (← `clusters_final.csv` + `cluster_fragilite.joblib`) | 1 ligne = 1 commune | `cluster`, `cluster_nom`, `niveau_fragilite` + features socio-mobilité |

---

## 2. Principes directeurs UX/UI (data-viz)

Le dashboard applique un socle de bonnes pratiques, transverses à toutes les visualisations :

1. **« Overview first, zoom & filter, details on demand »** (Shneiderman) : chaque onglet ouvre sur une synthèse,
   puis le filtrage et le drill-down révèlent le détail.
2. **Une question = une visualisation.** Chaque graphique répond à une question explicite, titrée comme telle
   (« Quelle part des trajets longue distance se fait de nuit ? »).
3. **Barre de filtres globale + cross-filtering.** Un filtre commun (pays, opérateur, mode, jour/nuit, distance,
   période) est persistant en haut de page ; cliquer un élément d'un graphique filtre les autres.
4. **Encodages sémantiques constants.** *Jour* = ambre `#E8A33D`, *Nuit* = indigo `#3B4CC0` **partout** ;
   échelle carbone séquentielle vert→rouge ; fragilité en séquentiel unique. La couleur ne change jamais de sens.
5. **Honnêteté visuelle.** Barres à axe zéro ; pas de camembert au-delà de 5 parts (donut jour/nuit = 2 parts OK) ;
   agrégats normalisés (par voyageur-km pour le CO₂) ; intervalles/incertitude affichés quand pertinent.
6. **Sobriété (data-ink ratio).** Pas d'effet 3D, grilles légères, libellés directs plutôt que légendes éloignées.
7. **Performance.** Toutes les agrégations sur les ~13M trajets sont faites **côté API/SQL** ; le front ne reçoit
   que des données agrégées ou paginées (jamais le brut). Les scatters massifs passent par échantillonnage ou hexbin.
8. **Accessibilité RGAA (transverse, cf. §3).** Voir section dédiée.
9. **Responsive & progressive disclosure.** Grille en cartes ré-agençables ; les détails s'ouvrent en panneau/modale.

### Système visuel (design tokens data-viz)

| Token | Usage | Valeur |
| --- | --- | --- |
| `--c-jour` | trains de jour | ambre `#E8A33D` |
| `--c-nuit` | trains de nuit | indigo `#3B4CC0` |
| `--seq-carbone` | échelle CO₂ | séquentiel vert→rouge (sobre) |
| `--seq-fragilite` | niveau de fragilité | séquentiel unique (clair→foncé) |
| `--cat-operateurs` | opérateurs | palette qualitative **daltonisme-safe** (Okabe–Ito) |
| `--seq-densite` | cartes de densité/volume | viridis |

Composants récurrents : **KPI card**, **barre de filtres**, **légende interactive cliquable**, **tooltip standard**
(libellé + valeur + unité), **bascule “Voir le tableau de données”** (équivalent textuel accessible de chaque graphe).

---

## 3. Accessibilité (RGAA) — règles transverses

- **Ne jamais coder l'information par la seule couleur** : ajouter motif/texture, icône ou libellé (ex. trains de nuit
  = indigo **+** icône lune ; barres avec étiquette de valeur).
- **Contraste AA** (≥ 4.5:1 texte, ≥ 3:1 éléments graphiques) ; palettes vérifiées daltonisme.
- **Équivalent non graphique** : chaque visualisation propose une **table de données** consultable (bascule), exportable
  CSV — sert d'alternative accessible et de preuve de transparence (exigence RGPD/qualité).
- **Navigation clavier complète** et **ARIA** : `role="img"` + `aria-label` décrivant la tendance ; focus visibles ;
  composants Dash interactifs étiquetés (`aria-label` sur filtres, tableaux avec en-têtes `<th scope>`).
- **Pas d'information transmise uniquement au survol** : les valeurs clés restent lisibles sans hover (étiquettes,
  table). Tooltips = complément, pas substitut.
- **Mouvement maîtrisé** : pas d'animation automatique non désactivable ; respect de `prefers-reduced-motion`.
- **Titres, langue, ordre de lecture** : titres de section hiérarchisés, `lang="fr"`, ordre DOM logique.

---

## 4. Organisation en onglets (navigation)

Architecture en **9 onglets**, ordonnés du général au spécifique, regroupés par **tâche utilisateur** (et non par
source de données). La barre de filtres est **globale** et transverse à tous les onglets analytiques.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  [ Barre de filtres globale : Pays · Opérateur · Mode · Jour/Nuit · Distance ] │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1.Vue d'ensemble │ 2.Trajets │ 3.Jour/Nuit │ 4.Opérateurs │ 5.Carbone │       │
│ 6.Territoires │ 7.Fragilité │ 8.Qualité des données │ 9.Supervision           │
└──────────────────────────────────────────────────────────────────────────────┘
```

| # | Onglet | Question centrale | Public visé |
| --- | --- | --- | --- |
| 1 | **Vue d'ensemble** | « Que dit le réseau d'un coup d'œil ? » | Tous (page d'atterrissage) |
| 2 | **Explorateur de trajets** | « Quels trajets existent et avec quelles caractéristiques ? » | Opérateurs, analystes |
| 3 | **Jour vs Nuit** | « Quel rôle jouent les trains de nuit ? » | Institutions, ONG (cœur ObRail) |
| 4 | **Opérateurs & lignes** | « Comment se comparent les opérateurs ? » | Opérateurs, institutions |
| 5 | **Empreinte carbone** | « Le train, alternative crédible à l'avion ? » | Institutions, ONG |
| 6 | **Territoires & couverture** | « Qui est bien/mal desservi ? » | Institutions, collectivités |
| 7 | **Fragilité territoriale** | « Quels territoires sont fragiles ? (modèle) » | Institutions, ONG |
| 8 | **Qualité des données** | « Peut-on faire confiance aux données ? » | Équipes internes ObRail |
| 9 | **Supervision** | « Le service est-il sain ? » | Équipes techniques ObRail |

> **Pourquoi cet ordre ?** On part de la synthèse (1), on donne l'outil d'exploration brute (2), puis les **trois récits
> métier** d'ObRail — jour/nuit (3), comparaison opérateurs (4), carbone/alternative avion (5) — avant la lecture
> **territoriale** (6) et **modèle** (7). Les onglets 8–9 sont les vues « confiance & exploitation » (qualité, santé).

---

## 5. Conventions d'API & DTO communs

- **Base URL** : `/api/v1`. Format **JSON**, dates **ISO 8601**, heures `HH:MM:SS`, parts en ratio `0..1`.
- **Documentation** : OpenAPI/Swagger auto (`/docs`). Validation des entrées par Pydantic ; erreurs normalisées.
- **Pagination** (enveloppe générique) :

```jsonc
Page<T> {
  items: T[],
  total: int,
  page: int,        // 1-based
  page_size: int,   // défaut 50, max 200
  pages: int
}
```

- **Filtre commun `TripFilter`** (query params, tous optionnels) — accepté par tous les endpoints d'agrégation de
  trajets, ce qui rend la **barre de filtres globale** universelle :

```jsonc
TripFilter (query) {
  mode?: string[],               // ex: ["train"]
  is_night?: bool,               // true=nuit, false=jour, absent=les deux
  departure_country?: string[],  // ISO-2, ex: ["FR","DE"]
  arrival_country?: string[],
  departure_city?: string,
  arrival_city?: string,
  agency_name?: string[],
  distance_min_km?: float,
  distance_max_km?: float,
  date_from?: date,              // recouvre service_start/end_date
  date_to?: date,
  cross_border?: bool            // departure_country != arrival_country
}
```

- **Erreur normalisée** :

```jsonc
ApiError { detail: string, code: string, field?: string }   // statuts 4xx/5xx
```

- **Types partagés** : `GeoPoint { lat: float, lon: float }`, `NiveauFragilite = "Faible" | "Modéré" | "Élevé" | …`.

---

## 6. Catalogue des visualisations (par onglet)

Chaque fiche : **question → type (+ justification UX) → encodage → interactions → accessibilité → endpoint(s) → DTO**.

### Onglet 1 — Vue d'ensemble

**V1.1 — Bandeau de KPI**
- **Question** : quels sont les chiffres-clés du réseau (sous filtre courant) ?
- **Type** : 8 *KPI cards* (valeur + libellé + micro-tendance). Lecture instantanée, hiérarchie typographique.
- **Encodage** : nombre + unité + sparkline optionnelle ; icône sémantique par carte.
- **Interactions** : se recalcule avec la barre de filtres globale ; clic = lien vers l'onglet détaillé.
- **Accessibilité** : chaque carte est un `<dl>` (terme/valeur), lisible lecteur d'écran ; pas de couleur seule.
- **Endpoint** : `GET /api/v1/stats/overview`

```jsonc
// → OverviewKPI
OverviewKPI {
  total_trajets: int,
  part_nuit: float,                 // 0..1
  nb_operateurs: int,
  nb_villes_desservies: int,
  nb_pays: int,
  part_transfrontalier: float,      // 0..1
  distance_mediane_km: float,
  co2_moyen_par_pkm: float,
  emissions_co2_totales_t: float    // tonnes
}
```

**V1.2 — Donut Jour / Nuit**
- **Question** : quelle est la part jour vs nuit ?
- **Type** : donut **2 parts** (exception légitime au “pas de camembert”), centre = % nuit en gros.
- **Encodage** : couleurs sémantiques jour/nuit + icône lune/soleil.
- **Interactions** : clic sur une part → applique le filtre `is_night` global.
- **Endpoint** : `GET /api/v1/stats/jour-nuit` → voir **V3.1** (`JourNuitCompare`).

**V1.3 — Carte de chaleur nationale des départs**
- **Question** : où partent les trajets ?
- **Type** : carte (hexbin/densité) des villes de départ pondérées par volume. Lecture géographique immédiate.
- **Encodage** : densité = viridis ; zoom/pan.
- **Interactions** : sélection d'une zone → filtre `departure_city`/zone.
- **Accessibilité** : table associée « top 20 villes de départ » comme équivalent.
- **Endpoint** : `GET /api/v1/trajets/flux?group=depart` → voir **V2.1** (`Flow`).

**V1.4 — Top 5 opérateurs (barres)**
- **Question** : qui opère le plus de trajets ?
- **Type** : barres horizontales triées (lecture des rangs).
- **Endpoint** : `GET /api/v1/stats/operateurs?limit=5` → voir **V4.1** (`OperateurStat`).

---

### Onglet 2 — Explorateur de trajets

**V2.1 — Carte des liaisons (arcs origine→destination)**
- **Question** : quelles liaisons relient quelles villes ?
- **Type** : *arc map* (lignes O-D) sur fond clair ; épaisseur = volume, couleur = jour/nuit.
- **Encodage** : arc épaisseur=`count`, couleur=part nuit, opacité pour densité.
- **Interactions** : hover = détail liaison ; clic = filtre la table ; jour/nuit togglable.
- **Accessibilité** : équivalent table (V2.2) ; arcs non superposés au survol (mise en évidence).
- **Endpoint** : `GET /api/v1/trajets/flux` (agrégation par couple de villes)

```jsonc
// query: TripFilter + group: "od" | "depart" | "arrivee" (défaut "od"), limit?: int
// → Flow[]
Flow {
  departure_city: string,
  departure: GeoPoint,
  arrival_city: string | null,      // null si group != "od"
  arrival: GeoPoint | null,
  count: int,
  part_nuit: float,                 // 0..1
  distance_moy_km: float,
  co2_moy_par_pkm: float
}
```

**V2.2 — Table des trajets (filtrable, triable, paginée)**
- **Question** : détail trajet par trajet ?
- **Type** : *data table* paginée serveur — colonnes triables, recherche, export CSV.
- **Interactions** : tri (`sort`), filtres locaux mappés sur `TripFilter`, clic ligne → V2.4.
- **Accessibilité** : table HTML native, en-têtes `scope`, pagination annoncée ARIA.
- **Endpoint** : `GET /api/v1/trajets`

```jsonc
// query: TripFilter + page, page_size, sort (ex: "-distance_km")
// → Page<TripListItem>
TripListItem {
  trip_id: string,
  mode: string,
  agency_name: string,
  route_short_name: string | null,
  departure_city: string,
  departure_country: string,
  arrival_city: string,
  arrival_country: string,
  departure_time: string,           // "HH:MM:SS"
  arrival_time: string,
  distance_km: float,
  is_night_train: bool,
  emissions_co2: float,             // kg pour le trajet
  co2_per_pkm: float
}
```

**V2.3 — Histogramme des distances**
- **Question** : comment se répartissent les distances (et la part nuit par tranche) ?
- **Type** : histogramme empilé jour/nuit ; révèle les trajets longue distance (cible trains de nuit).
- **Endpoint** : `GET /api/v1/stats/distance-distribution`

```jsonc
// query: TripFilter + bin_km?: float (défaut 100)
// → DistanceHistogram
DistanceHistogram {
  bin_km: float,
  bins: { min_km: float, max_km: float, count_jour: int, count_nuit: int }[]
}
```

**V2.4 — Détail d'un trajet (panneau details-on-demand)**
- **Question** : tout savoir sur un trajet précis ?
- **Type** : panneau latéral fiche (horaires, gares, calendrier de service, émissions).
- **Endpoint** : `GET /api/v1/trajets/{trip_id}`

```jsonc
// → TripDetail
TripDetail {
  trip_id: string, mode: string, agency_name: string,
  route_short_name: string | null, route_long_name: string | null,
  departure_station: string, departure_city: string, departure_country: string, departure_time: string,
  arrival_station: string,   arrival_city: string,   arrival_country: string,   arrival_time: string,
  service_start_date: date, service_end_date: date,
  days_of_week: string,             // ex "1000001" (bitmask Lun..Dim)
  is_night_train: bool,
  distance_km: float, co2_per_pkm: float, emissions_co2: float
}
```

---

### Onglet 3 — Jour vs Nuit  *(cœur métier ObRail)*

**V3.1 — Comparateur apparié jour vs nuit**
- **Question** : comment jour et nuit diffèrent sur les indicateurs clés ?
- **Type** : *paired bars* / tableau comparatif (volume, distance moyenne, CO₂/pkm, part transfrontalière).
- **Endpoint** : `GET /api/v1/stats/jour-nuit`

```jsonc
// query: TripFilter
// → JourNuitCompare
JourNuitCompare {
  jour: SegmentStat,
  nuit: SegmentStat
}
SegmentStat {
  nb_trajets: int,
  part: float,                      // 0..1 du total
  distance_moy_km: float,
  distance_med_km: float,
  co2_moy_par_pkm: float,
  part_transfrontalier: float
}
```

**V3.2 — Heatmap heure de départ × jour de semaine**
- **Question** : quand partent les trains (rythme jour/nuit) ?
- **Type** : *heatmap* 24h × 7j ; révèle le creux nocturne et les pics. Bascule jour/nuit/tous.
- **Encodage** : intensité = nb trajets (viridis) ; axes lisibles.
- **Accessibilité** : table matricielle équivalente ; valeurs au focus clavier cellule par cellule.
- **Endpoint** : `GET /api/v1/stats/departs-heatmap`

```jsonc
// query: TripFilter
// → DepartHeatmap
DepartHeatmap {
  cells: { hour: int, dow: int, count: int }[]   // hour 0..23, dow 0=Lun..6=Dim
}
```

**V3.3 — Part de nuit par tranche de distance**

> V3.3 OU V3.1 selon résultat

- **Question** : la nuit gagne-t-elle sur la longue distance ?
- **Type** : barres empilées 100% par tranche de distance (part nuit croissante attendue).
- **Endpoint** : `GET /api/v1/stats/jour-nuit/par-distance`

```jsonc
// query: TripFilter + bin_km?
// → { bins: { min_km: float, max_km: float, part_nuit: float, count: int }[] }
```

**V3.4 — Sankey des flux (segment → distance → transfrontalier)**

> A voir selon pertinance

- **Question** : comment se structurent les flux jour/nuit ?
- **Type** : *Sankey* (original) reliant `Jour|Nuit` → tranches de distance → `National|Transfrontalier`.
- **Accessibilité** : table des flux (source, cible, valeur) en équivalent.
- **Endpoint** : `GET /api/v1/stats/sankey`

```jsonc
// query: TripFilter + dimensions: string[] (ex: ["segment","distance_band","cross_border"])
// → Sankey
Sankey {
  nodes: { id: string, label: string }[],
  links: { source: string, target: string, value: int }[]
}
```

---

### Onglet 4 — Opérateurs & lignes

**V4.1 — Classement des opérateurs**
- **Question** : qui opère le plus, et avec quelle empreinte ?
- **Type** : barres triées + métrique bascule (volume / CO₂ moyen / part nuit / nb pays).
- **Endpoint** : `GET /api/v1/stats/operateurs`

```jsonc
// query: TripFilter + sort_by?: "volume"|"co2"|"part_nuit" + limit?
// → OperateurStat[]
OperateurStat {
  agency_name: string,
  nb_trajets: int,
  part_nuit: float,
  distance_moy_km: float,
  co2_moy_par_pkm: float,
  emissions_co2_totales_t: float,
  nb_lignes: int,
  nb_pays_desservis: int
}
```

**V4.2 — Treemap volumes (opérateur → mode → pays)**
- **Question** : comment le volume se répartit hiérarchiquement ?
- **Type** : *treemap* ; lecture des proportions imbriquées en un écran.
- **Endpoint** : `GET /api/v1/stats/operateurs/treemap`

```jsonc
// query: TripFilter + levels: string[] (défaut ["agency_name","mode","departure_country"])
// → TreeNode (récursif)
TreeNode { label: string, value: int, children?: TreeNode[] }
```

**V4.3 — Fiche profil opérateur (radar)**

> Priorité P10

- **Question** : quelle est la “signature” d'un opérateur ?
- **Type** : *radar* normalisé (part nuit, distance, CO₂, couverture pays, nb lignes) + KPI.
- **Endpoint** : `GET /api/v1/operateurs/{agency_name}/profil`

```jsonc
// → OperateurProfil
OperateurProfil {
  agency_name: string,
  kpi: OperateurStat,
  radar: { axe: string, valeur_normalisee: float }[],   // 0..1
  top_liaisons: Flow[]
}
```

---

### Onglet 5 — Empreinte carbone (train vs avion)

**V5.1 — Compteur « CO₂ évité vs avion »**
- **Question** : combien d'émissions le train économise-t-il face à l'avion ?
- **Type** : grand *number callout* + barres comparées (train vs estimation avion) par tranche de distance.
- **Note méthodo** : facteur avion paramétrable, **affiché** (transparence) ; comparaison à voyageur-km.
- **Endpoint** : `GET /api/v1/stats/co2/comparaison-avion`

```jsonc
// query: TripFilter + facteur_avion_g_par_pkm?: float (défaut documenté)
// → ComparaisonAvion
ComparaisonAvion {
  facteur_avion_g_par_pkm: float,
  co2_train_total_t: float,
  co2_avion_estime_t: float,
  co2_evite_t: float,
  par_tranche: { min_km: float, max_km: float, train_t: float, avion_t: float }[]
}
```

**V5.2 — Distance × intensité carbone (densité)**
- **Question** : l'intensité carbone varie-t-elle avec la distance/le mode ?
- **Type** : *hexbin/scatter densité* (distance_km × co2_per_pkm), couleur = mode ou jour/nuit. Agrégé (pas 13M points).
- **Endpoint** : `GET /api/v1/stats/co2/scatter`

```jsonc
// query: TripFilter + x_bins?: int, y_bins?: int
// → { bins: { x_km: float, y_co2_pkm: float, count: int }[] }
```

**V5.3 — Distribution du CO₂/pkm par mode**
- **Question** : quelle dispersion d'intensité carbone par mode ?
- **Type** : *box plot / violon* par mode (médiane, quartiles, extrêmes).
- **Endpoint** : `GET /api/v1/stats/co2/par-mode`

```jsonc
// query: TripFilter
// → { modes: { mode: string, min: float, q1: float, mediane: float, q3: float, max: float, count: int }[] }
```


---

### Onglet 6 — Territoires & couverture ferroviaire

**V6.1 — Carte de la couverture ferroviaire**
- **Question** : quelles communes ont une gare / quel niveau d'accès ?
- **Type** : carte points/choroplèthe ; dimension bascule (`has_gare`, `accessibilite_ord`, `nb_trajets_total`,
  `dist_gare_min_m`).
- **Encodage** : séquentiel ; taille = population ; lasso de sélection.
- **Accessibilité** : table « communes » filtrable comme équivalent ; bascule dimension étiquetée.
- **Endpoint** : `GET /api/v1/villes/carte`

```jsonc
// query: GeoFilter { code_dept?, code_region?, has_gare?, dimension: string }
// → VilleGeoPoint[]
VilleGeoPoint {
  citycode: string,
  city_name: string,
  geo: GeoPoint,
  population: float,
  valeur: float,        // valeur de la dimension demandée
  has_gare: bool
}
```

**V6.2 — Couverture par département / région**
- **Question** : quels territoires sont les mieux desservis ?
- **Type** : barres triées ou *small multiples* ; bascule maille (département/région).
- **Endpoint** : `GET /api/v1/stats/couverture`

```jsonc
// query: by: "code_dept"|"code_region"
// → { mailles: { cle: string, nb_communes: int, taux_avec_gare: float,
//                nb_trajets_total: int, accessibilite_moy: float }[] }
```

**V6.4 — Amplitude de service (premier/dernier départ)**
- **Question** : jusqu'à quelle heure le territoire est-il desservi ?
- **Type** : distribution de `amplitude_moy_h` + indicateur `dernier_depart_apres_minuit`.
- **Endpoint** : `GET /api/v1/stats/amplitude` → `{ bins: {...}[], part_apres_minuit: float }`.

**V6.5 — Détail commune**
- **Endpoint** : `GET /api/v1/villes/{citycode}` → `VilleDetail` (toutes colonnes `villes` + cluster/fragilité liés).

---

### Onglet 7 — Fragilité territoriale  *(modèle de clustering)*

**V7.1 — Carte des clusters**
- **Question** : comment se répartissent les profils de territoires ?
- **Type** : carte points colorés par `cluster_nom` (palette qualitative) ; légende = libellés de clusters.
- **Endpoint** : `GET /api/v1/clusters/carte`

```jsonc
// query: GeoFilter
// → ClusterGeoPoint[]
ClusterGeoPoint {
  citycode: string, city_name: string, geo: GeoPoint,
  cluster: int, cluster_nom: string, niveau_fragilite: NiveauFragilite
}
```

**V7.2 — Profils de clusters (coordonnées parallèles)**
- **Question** : qu'est-ce qui caractérise chaque cluster ?
- **Type** : *parallel coordinates* sur features normalisées (revenu, taux_sans_voiture, part_65plus, densité,
  nb_trajets, dist_gare…). Vue d'ensemble multivariée. Radar par cluster en complément.
- **Endpoint** : `GET /api/v1/clusters/profils`

```jsonc
// → ClusterProfil[]
ClusterProfil {
  cluster: int,
  cluster_nom: string,
  niveau_fragilite: NiveauFragilite,
  effectif: int,
  features: { nom: string, moyenne: float, moyenne_normalisee: float }[]   // normalisée 0..1
}
```

**V7.3 — Répartition de la fragilité par région**

> Priorité P10

- **Question** : où se concentre la fragilité ?
- **Type** : barres empilées par région selon `niveau_fragilite`.
- **Endpoint** : `GET /api/v1/stats/fragilite`

```jsonc
// query: by: "code_region"|"code_dept"
// → { mailles: { cle: string, repartition: { niveau: NiveauFragilite, nb: int }[] }[] }
```

**V7.4 — Liste / effectifs des clusters**
- **Type** : cartes ou barres des effectifs par cluster (point d'entrée vers V7.2).
- **Endpoint** : `GET /api/v1/clusters`

```jsonc
// → ClusterSummary[]
ClusterSummary { cluster: int, cluster_nom: string, niveau_fragilite: NiveauFragilite, effectif: int }
```

**V7.5 — Simulateur de fragilité (modèle live)**
- **Question** : à quel cluster appartiendrait un territoire donné ?
- **Type** : formulaire (features) → résultat cluster + niveau (utilise `cluster_fragilite.joblib`).
- **Accessibilité** : formulaire étiqueté, résultat annoncé (ARIA live region).
- **Endpoint** : `POST /api/v1/fragilite/predict`

```jsonc
// body: FragiliteFeatures (features attendues par le modèle)
FragiliteFeatures {
  densite_pop_km2: float, revenu_median_uc: float, voitures_par_menage: float,
  taux_sans_voiture: float, part_65plus: float, distance_dom_trav_med_km: float,
  has_gare: bool, accessibilite_ord: float, dist_gare_min_m: float,
  nb_trajets_total: float, nb_lignes_total: float, amplitude_moy_h: float, population: float
}
// → FragilitePrediction
FragilitePrediction { cluster: int, cluster_nom: string, niveau_fragilite: NiveauFragilite }
```

---

### Onglet 8 — Qualité des données

**V8.1 — Complétude par colonne**
- **Question** : quelles colonnes ont des valeurs manquantes ?
- **Type** : barres horizontales du **% de complétude** par colonne et par table.
- **Endpoint** : `GET /api/v1/qualite/completude`

```jsonc
// query: table: "trajets"|"villes"|"clusters"
// → { table: string, colonnes: { nom: string, taux_complet: float, nb_nuls: int }[], nb_lignes: int }
```

**V8.2 — Anomalies & doublons**
- **Question** : quelles incohérences subsistent (doublons, codes gares manquants, horaires invalides) ?
- **Type** : cartes-compteurs + table de détail.
- **Endpoint** : `GET /api/v1/qualite/anomalies`

```jsonc
// → { anomalies: { type: string, libelle: string, nb: int, severite: "info"|"warn"|"error" }[] }
```

**V8.4 — Volumétrie par source**
- **Type** : barres du nombre de trajets par `source`/`agency_name`.
- **Endpoint** : `GET /api/v1/qualite/volumetrie` → `{ sources: { cle: string, nb: int }[] }`.

---

### Onglet 9 — Supervision  *(monitoring — phase ultérieure)*

> Alimenté par la stack monitoring (Prometheus/Grafana). Côté dashboard : panneaux
> d'état + embarquement de tableaux Grafana.

**V9.1 — État de santé du service**
- **Type** : feux d'état (API, BDD), badges UP/DOWN, dernière vérification.
- **Endpoint** : `GET /health` (déjà au MVP) ; `GET /api/v1/health/details` → `{ services: { nom, statut, latence_ms }[] }`.

**V9.2 — Métriques (latence, taux d'erreurs, volumes)**
- **Type** : séries temporelles (latence p50/p95, taux d'erreurs), jauges.
- **Source** : `GET /metrics` (format Prometheus) scrappé par Prometheus, restitué via Grafana embarqué.

**V9.3 — Journal applicatif & anomalies**
- **Type** : table des derniers événements/incidents (niveau, horodatage, message).
- **Source** : logs structurés → backend de logs (déféré).

---

## 7. Récapitulatif des endpoints

| Endpoint | Méthode | Onglet(s) | DTO réponse |
| --- | --- | --- | --- |
| `/api/v1/stats/overview` | GET | 1 | `OverviewKPI` |
| `/api/v1/stats/jour-nuit` | GET | 1, 3 | `JourNuitCompare` |
| `/api/v1/stats/jour-nuit/par-distance` | GET | 3 | bins part nuit |
| `/api/v1/stats/departs-heatmap` | GET | 3 | `DepartHeatmap` |
| `/api/v1/stats/sankey` | GET | 3 | `Sankey` |
| `/api/v1/trajets` | GET | 2 | `Page<TripListItem>` |
| `/api/v1/trajets/{trip_id}` | GET | 2 | `TripDetail` |
| `/api/v1/trajets/flux` | GET | 1, 2 | `Flow[]` |
| `/api/v1/stats/distance-distribution` | GET | 2 | `DistanceHistogram` |
| `/api/v1/stats/operateurs` | GET | 1, 4 | `OperateurStat[]` |
| `/api/v1/stats/operateurs/treemap` | GET | 4 | `TreeNode` |
| `/api/v1/operateurs/{agency_name}/profil` | GET | 4 | `OperateurProfil` |
| `/api/v1/stats/co2/comparaison-avion` | GET | 5 | `ComparaisonAvion` |
| `/api/v1/stats/co2/scatter` | GET | 5 | bins densité |
| `/api/v1/stats/co2/par-mode` | GET | 5 | box stats |
| `/api/v1/stats/co2` | GET | 5 | groupes émissions |
| `/api/v1/villes/carte` | GET | 6 | `VilleGeoPoint[]` |
| `/api/v1/villes` | GET | 6 | `Page<VilleListItem>` |
| `/api/v1/villes/{citycode}` | GET | 6 | `VilleDetail` |
| `/api/v1/stats/couverture` | GET | 6 | mailles couverture |
| `/api/v1/stats/amplitude` | GET | 6 | distribution amplitude |
| `/api/v1/clusters` | GET | 7 | `ClusterSummary[]` |
| `/api/v1/clusters/carte` | GET | 7 | `ClusterGeoPoint[]` |
| `/api/v1/clusters/profils` | GET | 7 | `ClusterProfil[]` |
| `/api/v1/stats/fragilite` | GET | 7 | répartition fragilité |
| `/api/v1/fragilite/predict` | POST | 7 | `FragilitePrediction` |
| `/api/v1/qualite/completude` | GET | 8 | complétude colonnes |
| `/api/v1/qualite/anomalies` | GET | 8 | anomalies |
| `/api/v1/qualite/couverture-temporelle` | GET | 8 | périodes |
| `/api/v1/qualite/volumetrie` | GET | 8 | volumétrie sources |
| `/health`, `/api/v1/health/details`, `/metrics` | GET | 9 | santé / métriques |

> **Note d'implémentation** : tous les endpoints `/stats/*` et `/trajets/flux` acceptent `TripFilter` → la barre de
> filtres globale est branchée une seule fois côté front et propage l'état à toutes les visualisations (cross-filter).

---

## 8. Synthèse couverture du besoin (traçabilité sujet → onglets)

| Besoin ObRail (sujet) | Couvert par |
| --- | --- |
| Consultation & filtrage des trajets | Onglet 2 (+ barre de filtres globale) |
| Indicateurs clés (jour/nuit, volumes opérateurs) | Onglets 1, 3, 4 |
| Train alternative à l'avion / mobilité durable | Onglet 5 (CO₂ évité) |
| Couverture ferroviaire & territoires | Onglet 6 |
| Modèle (fragilité / clustering) | Onglet 7 |
| Qualité & transparence des données (RGPD) | Onglet 8 + tables équivalentes partout |
| Supervision / santé du service | Onglet 9 |
| Accessibilité RGAA | §3 (transverse) |
