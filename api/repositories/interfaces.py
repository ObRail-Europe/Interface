"""Abstractions de la couche d'accès aux données.

Les services dépendent de ces `Protocol`, pas de SQLAlchemy
"""

from dataclasses import dataclass
from typing import Protocol


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


class TrajetRepository(Protocol):
    """Accès aux trajets de l'onglet « Explorateur de trajets »."""

    def top_liaisons(self, limit: int) -> list[LiaisonAggregate]: ...
