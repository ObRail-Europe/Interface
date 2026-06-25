"""Tests unitaires du service Vue d'ensemble."""

from repositories.interfaces import OverviewAggregates
from services.overview_service import OverviewService


class FakeStatsRepository:
    """Doublure en mémoire de `StatsRepository` (démontre l'inversion de dépendance)."""

    def __init__(self, aggregates: OverviewAggregates) -> None:
        self._aggregates = aggregates

    def overview_aggregates(self) -> OverviewAggregates:
        return self._aggregates


def test_overview_computes_ratios_and_units() -> None:
    agg = OverviewAggregates(
        total_trajets=10,
        nb_nuit=3,
        nb_operateurs=4,
        nb_villes_desservies=8,
        nb_pays=3,
        nb_transfrontalier=2,
        distance_mediane_km=200.0,
        co2_moyen_par_pkm=2.5,
        emissions_co2_totales_g=5_000_000,
    )
    kpi = OverviewService(FakeStatsRepository(agg)).get_overview()

    assert kpi.total_trajets == 10
    assert kpi.part_nuit == 0.3
    assert kpi.part_transfrontalier == 0.2
    assert kpi.emissions_co2_totales_t == 5.0


def test_overview_handles_empty_dataset() -> None:
    agg = OverviewAggregates(0, 0, 0, 0, 0, 0, None, None, 0)
    kpi = OverviewService(FakeStatsRepository(agg)).get_overview()

    assert kpi.total_trajets == 0
    assert kpi.part_nuit == 0.0  # pas de division par zéro
    assert kpi.distance_mediane_km is None
