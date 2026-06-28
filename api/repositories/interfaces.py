"""Abstractions de la couche d'accès aux données.

Les services dépendent de ces `Protocol`, pas de SQLAlchemy
"""

from dataclasses import dataclass
from typing import Protocol

from models import Trajet


@dataclass(frozen=True)
class OverviewAggregates:
    """Agrégats bruts des trajets (avant calcul des ratios, fait dans le service)."""

    total_trajets: int
    nb_nuit: int
    nb_operateurs: int
    nb_villes_desservies: int
    nb_pays: int
    nb_transfrontalier: int
    distance_mediane_km: float | None
    co2_moyen_par_pkm: float | None
    emissions_co2_totales_g: float


@dataclass(frozen=True)
class JourNuitCounts:
    """Décompte des trajets de jour et de nuit."""

    nb_jour: int
    nb_nuit: int


@dataclass(frozen=True)
class OperateurCount:
    """Volume (et part de nuit) d'un opérateur."""

    agency_name: str
    nb_trajets: int
    nb_nuit: int


@dataclass(frozen=True)
class DepartAggregate:
    """Ville de départ géolocalisée et son volume de trajets."""

    citycode: str
    city_name: str
    lat: float
    lon: float
    nb_trajets: int


class StatsRepository(Protocol):
    """Accès aux statistiques agrégées des trajets."""

    def overview_aggregates(self) -> OverviewAggregates: ...

    def jour_nuit_counts(self) -> JourNuitCounts: ...

    def top_operateurs(self, limit: int) -> list[OperateurCount]: ...

    def departs(self) -> list[DepartAggregate]: ...


@dataclass(frozen=True)
class LiaisonAggregate:
    """Liaison origine→destination agrégée (volume, part de nuit, moyennes)."""

    departure_city: str
    departure_lat: float
    departure_lon: float
    arrival_city: str
    arrival_lat: float
    arrival_lon: float
    nb_trajets: int
    nb_nuit: int
    distance_moy_km: float | None
    co2_moy_par_pkm: float | None


@dataclass(frozen=True)
class TrajetFilter:
    """Critères de filtrage de la table des trajets (couche domaine)."""

    mode: str | None = None
    is_night: bool | None = None
    departure_city: str | None = None
    arrival_city: str | None = None
    agency_name: str | None = None
    departure_country: str | None = None
    arrival_country: str | None = None
    distance_min_km: float | None = None
    distance_max_km: float | None = None


@dataclass(frozen=True)
class DistanceBinAggregate:
    """Tranche de distance avec décompte jour/nuit."""

    min_km: float
    max_km: float
    count_jour: int
    count_nuit: int


class TrajetRepository(Protocol):
    """Accès aux trajets de l'onglet « Explorateur de trajets »."""

    def top_liaisons(self, limit: int) -> list[LiaisonAggregate]: ...

    def list_trajets(
        self,
        criteria: TrajetFilter,
        sort_field: str,
        sort_desc: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Trajet], int]: ...

    def distance_histogram(self, bin_km: int) -> list[DistanceBinAggregate]: ...

    def get_trajet(self, trajet_id: int) -> Trajet | None: ...


@dataclass(frozen=True)
class Co2BandAggregate:
    """Agrégats train d'une tranche de distance (base du comparatif train vs avion)."""

    min_km: float
    max_km: float
    nb_trajets: int
    train_pkm: float  # somme des distances (voyageur-km) des trajets train de la tranche
    train_emissions_g: float


@dataclass(frozen=True)
class CarbonDensityCell:
    """Cellule d'histogramme 2D (distance × intensité carbone) d'un mode."""

    mode: str
    x_km: float  # centre du bin de distance
    y_co2_pkm: float  # centre du bin d'intensité (g/pkm)
    count: int


@dataclass(frozen=True)
class ModeDistributionAggregate:
    """Quartiles et extrêmes du CO₂/pkm d'un mode (box plot)."""

    mode: str
    count: int
    co2_min: float
    co2_q1: float
    co2_median: float
    co2_q3: float
    co2_max: float
    co2_moy: float


class CarbonRepository(Protocol):
    """Accès aux agrégats carbone (train vs avion) des vues matérialisées."""

    def comparaison_bands(self) -> list[Co2BandAggregate]: ...

    def carbon_density(self) -> list[CarbonDensityCell]: ...

    def co2_distribution(self) -> list[ModeDistributionAggregate]: ...


@dataclass(frozen=True)
class VilleGeoAggregate:
    """Commune géolocalisée et la valeur de la dimension cartographiée."""

    citycode: str
    city_name: str
    lat: float
    lon: float
    population: float | None
    valeur: float | None
    has_gare: bool | None


@dataclass(frozen=True)
class CouvertureMailleAggregate:
    """Couverture agrégée d'une maille (département ou région)."""

    cle: str
    nb_communes: int
    taux_avec_gare: float
    nb_trajets_total: int
    accessibilite_moy: float | None


@dataclass(frozen=True)
class AmplitudeBinAggregate:
    """Tranche d'amplitude de service (heures) et nombre de communes."""

    min_h: float
    max_h: float
    nb_communes: int


@dataclass(frozen=True)
class AmplitudeAggregate:
    """Distribution de l'amplitude de service + part des communes desservies après minuit."""

    bins: list[AmplitudeBinAggregate]
    part_apres_minuit: float


class TerritoireRepository(Protocol):
    """Accès aux données de l'onglet « Territoires & couverture ».

    La source est la table `villes` (~10k lignes, colonnes pré-calculées) : les lectures
    sont directes - pas de vue matérialisée (sur-dimensionnée ici), et les colonnes
    filtrées (`code_dept`, `code_region`, `has_gare`) sont déjà indexées au schéma.
    """

    def villes_carte(
        self,
        dimension: str,
        code_dept: str | None,
        code_region: str | None,
        has_gare: bool | None,
    ) -> list[VilleGeoAggregate]: ...

    def couverture(self, by: str) -> list[CouvertureMailleAggregate]: ...

    def amplitude(self, bin_h: float) -> AmplitudeAggregate: ...


@dataclass(frozen=True)
class ClusterGeoAggregate:
    """Commune géolocalisée et son cluster de fragilité (V7.1)."""

    citycode: str | None
    city_name: str
    lat: float
    lon: float
    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None


@dataclass(frozen=True)
class ClusterSummaryAggregate:
    """Effectif et libellés d'un cluster (V7.4)."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None
    effectif: int


@dataclass(frozen=True)
class ClusterProfilAggregate:
    """Profil d'un cluster : effectif + moyennes brutes par feature (V7.2)."""

    cluster: int
    cluster_nom: str | None
    niveau_fragilite: str | None
    effectif: int
    feature_means: dict[str, float | None]


@dataclass(frozen=True)
class FragiliteMailleAggregate:
    """Répartition des niveaux de fragilité dans une maille (V7.3)."""

    cle: str
    repartition: dict[str, int]  # niveau_fragilite -> nombre de communes


class ClusterRepository(Protocol):
    """Accès aux données de l'onglet « Fragilité territoriale ».

    Source : table `clusters` (~10k lignes, déjà indexée sur `cluster`,
    `niveau_fragilite`, `citycode`).
    """

    def clusters_carte(
        self, code_dept: str | None, code_region: str | None, has_gare: bool | None
    ) -> list[ClusterGeoAggregate]: ...

    def cluster_summaries(self) -> list[ClusterSummaryAggregate]: ...

    def cluster_profils(self, features: list[str]) -> list[ClusterProfilAggregate]: ...

    def fragilite_par_maille(self, by: str) -> list[FragiliteMailleAggregate]: ...


@dataclass(frozen=True)
class ColonneCompletudeAggregate:
    """Complétude d'une colonne : nombre de NULLs sur le total de lignes (V8.1)."""

    colonne: str
    nb_nuls: int
    nb_lignes: int


@dataclass(frozen=True)
class AnomalieAggregate:
    """Compteur d'un type d'anomalie (V8.2)."""

    type: str
    libelle: str
    nb: int
    severite: str


@dataclass(frozen=True)
class SourceVolumeAggregate:
    """Volume de trajets d'une source (V8.4)."""

    cle: str
    nb: int


class QualiteRepository(Protocol):
    """Accès aux audits qualité (vues matérialisées sur ~13M trajets)."""

    def completude(self, table: str) -> list[ColonneCompletudeAggregate]: ...

    def anomalies(self) -> list[AnomalieAggregate]: ...

    def volumetrie(self) -> list[SourceVolumeAggregate]: ...
