"""Cas d'usage de l'onglet « Vue d'ensemble ».

Le service porte la logique métier (ratios, conversions d'unités) et dépend de
l'abstraction `StatsRepository`, pas d'une implémentation concrète.
"""

from repositories.interfaces import StatsRepository
from schemas.depart import DepartPoint
from schemas.jour_nuit import JourNuitSplit, SegmentStat
from schemas.operateur import OperateurStat
from schemas.overview import OverviewKPI

_GRAMMES_PAR_TONNE = 1_000_000


def _ratio(part: int, total: int) -> float:
    return part / total if total else 0.0


class OverviewService:
    """Construit les indicateurs de la vue d'ensemble à partir des agrégats bruts."""

    def __init__(self, repository: StatsRepository) -> None:
        self._repository = repository

    def get_overview(self) -> OverviewKPI:
        agg = self._repository.overview_aggregates()
        total = agg.total_trajets
        return OverviewKPI(
            total_trajets=total,
            part_nuit=_ratio(agg.nb_nuit, total),
            nb_operateurs=agg.nb_operateurs,
            nb_villes_desservies=agg.nb_villes_desservies,
            nb_pays=agg.nb_pays,
            part_transfrontalier=_ratio(agg.nb_transfrontalier, total),
            distance_mediane_km=agg.distance_mediane_km,
            co2_moyen_par_pkm=agg.co2_moyen_par_pkm,
            emissions_co2_totales_t=agg.emissions_co2_totales_g / _GRAMMES_PAR_TONNE,
        )

    def get_jour_nuit(self) -> JourNuitSplit:
        counts = self._repository.jour_nuit_counts()
        total = counts.nb_jour + counts.nb_nuit
        return JourNuitSplit(
            jour=SegmentStat(nb_trajets=counts.nb_jour, part=_ratio(counts.nb_jour, total)),
            nuit=SegmentStat(nb_trajets=counts.nb_nuit, part=_ratio(counts.nb_nuit, total)),
        )

    def get_top_operateurs(self, limit: int = 5) -> list[OperateurStat]:
        return [
            OperateurStat(
                agency_name=op.agency_name,
                nb_trajets=op.nb_trajets,
                part_nuit=_ratio(op.nb_nuit, op.nb_trajets),
            )
            for op in self._repository.top_operateurs(limit)
        ]

    def get_departs(self) -> list[DepartPoint]:
        return [
            DepartPoint(
                citycode=d.citycode,
                city_name=d.city_name,
                lat=d.lat,
                lon=d.lon,
                nb_trajets=d.nb_trajets,
            )
            for d in self._repository.departs()
        ]
