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
    x_km: float  # borne basse du bin de distance
    y_co2_pkm: float  # borne basse du bin d'intensité (g/pkm)
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
