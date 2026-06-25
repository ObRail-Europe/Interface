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


class StatsRepository(Protocol):
    """Accès aux statistiques agrégées des trajets."""

    def overview_aggregates(self) -> OverviewAggregates: ...
