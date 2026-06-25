"""Tests unitaires du service Vue d'ensemble."""

from repositories.interfaces import JourNuitCounts, OperateurCount, OverviewAggregates
from services.overview_service import OverviewService


class FakeStatsRepository:
    """Doublure en mémoire de `StatsRepository` (démontre l'inversion de dépendance)."""

    def __init__(
        self,
        *,
        aggregates: OverviewAggregates | None = None,
        jour_nuit: JourNuitCounts | None = None,
        operateurs: list[OperateurCount] | None = None,
    ) -> None:
        self._aggregates = aggregates
        self._jour_nuit = jour_nuit
        self._operateurs = operateurs or []

    def overview_aggregates(self) -> OverviewAggregates:
        assert self._aggregates is not None
        return self._aggregates

    def jour_nuit_counts(self) -> JourNuitCounts:
        assert self._jour_nuit is not None
        return self._jour_nuit

    def top_operateurs(self, limit: int) -> list[OperateurCount]:
        return self._operateurs[:limit]


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
    kpi = OverviewService(FakeStatsRepository(aggregates=agg)).get_overview()

    assert kpi.total_trajets == 10
    assert kpi.part_nuit == 0.3
    assert kpi.part_transfrontalier == 0.2
    assert kpi.emissions_co2_totales_t == 5.0


def test_overview_handles_empty_dataset() -> None:
    agg = OverviewAggregates(0, 0, 0, 0, 0, 0, None, None, 0)
    kpi = OverviewService(FakeStatsRepository(aggregates=agg)).get_overview()

    assert kpi.total_trajets == 0
    assert kpi.part_nuit == 0.0  # pas de division par zéro
    assert kpi.distance_mediane_km is None


def test_jour_nuit_computes_parts() -> None:
    repo = FakeStatsRepository(jour_nuit=JourNuitCounts(nb_jour=12, nb_nuit=3))
    split = OverviewService(repo).get_jour_nuit()

    assert split.nuit.nb_trajets == 3
    assert split.nuit.part == 0.2
    assert split.jour.part == 0.8


def test_top_operateurs_computes_part_nuit_and_limits() -> None:
    repo = FakeStatsRepository(
        operateurs=[
            OperateurCount("SNCF", nb_trajets=10, nb_nuit=2),
            OperateurCount("ÖBB", nb_trajets=4, nb_nuit=4),
        ]
    )
    result = OverviewService(repo).get_top_operateurs(limit=1)

    assert len(result) == 1  # le repository tronque selon limit
    assert result[0].agency_name == "SNCF"
    assert result[0].part_nuit == 0.2
