"""Cas d'usage de l'onglet « Vue d'ensemble ».

Le service porte la logique métier (ratios, conversions d'unités) et dépend de
l'abstraction `StatsRepository`, pas d'une implémentation concrète.
"""

from repositories.interfaces import StatsRepository
from schemas.overview import OverviewKPI

_GRAMMES_PAR_TONNE = 1_000_000


class OverviewService:
    """Construit les indicateurs de la vue d'ensemble à partir des agrégats bruts."""

    def __init__(self, repository: StatsRepository) -> None:
        self._repository = repository

    def get_overview(self) -> OverviewKPI:
        agg = self._repository.overview_aggregates()
        total = agg.total_trajets or 0
        return OverviewKPI(
            total_trajets=total,
            part_nuit=agg.nb_nuit / total if total else 0.0,
            nb_operateurs=agg.nb_operateurs,
            nb_villes_desservies=agg.nb_villes_desservies,
            nb_pays=agg.nb_pays,
            part_transfrontalier=agg.nb_transfrontalier / total if total else 0.0,
            distance_mediane_km=agg.distance_mediane_km,
            co2_moyen_par_pkm=agg.co2_moyen_par_pkm,
            emissions_co2_totales_t=agg.emissions_co2_totales_g / _GRAMMES_PAR_TONNE,
        )
