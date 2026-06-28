"""Tests unitaires du service Fragilité (repository en mémoire, sans base)."""

from repositories.interfaces import (
    ClusterGeoAggregate,
    ClusterProfilAggregate,
    ClusterSummaryAggregate,
    FragiliteMailleAggregate,
)
from services.fragilite_service import FragiliteService


class FakeClusterRepository:
    """Doublure en mémoire de `ClusterRepository`."""

    def __init__(
        self,
        carte: list[ClusterGeoAggregate] | None = None,
        summaries: list[ClusterSummaryAggregate] | None = None,
        profils: list[ClusterProfilAggregate] | None = None,
        mailles: list[FragiliteMailleAggregate] | None = None,
    ) -> None:
        self._carte = carte or []
        self._summaries = summaries or []
        self._profils = profils or []
        self._mailles = mailles or []

    def clusters_carte(
        self, code_dept: str | None, code_region: str | None, has_gare: bool | None
    ) -> list[ClusterGeoAggregate]:
        return self._carte

    def cluster_summaries(self) -> list[ClusterSummaryAggregate]:
        return self._summaries

    def cluster_profils(self, features: list[str]) -> list[ClusterProfilAggregate]:
        return self._profils

    def fragilite_par_maille(self, by: str) -> list[FragiliteMailleAggregate]:
        return self._mailles


def test_get_carte_maps_clusters() -> None:
    repo = FakeClusterRepository(
        carte=[ClusterGeoAggregate("75056", "Paris", 48.85, 2.35, 0, "c0", "Élevée")]
    )
    points = FragiliteService(repo).get_carte()
    assert points[0].geo.lat == 48.85
    assert points[0].cluster == 0
    assert points[0].niveau_fragilite == "Élevée"


def test_get_profils_normalizes_per_feature() -> None:
    repo = FakeClusterRepository(
        profils=[
            ClusterProfilAggregate(0, "c0", "Faible", 6, {"revenu_median_uc": 30000.0}),
            ClusterProfilAggregate(1, "c1", "Élevée", 2, {"revenu_median_uc": 10000.0}),
            ClusterProfilAggregate(2, "c2", "Modérée", 1, {"revenu_median_uc": 20000.0}),
        ]
    )
    profils = FragiliteService(repo).get_profils()
    by_cluster = {p.cluster: p for p in profils}
    revenu = {p.cluster: p.features[0] for p in profils}  # 1re feature = revenu_median_uc
    assert revenu[0].moyenne_normalisee == 1.0  # max -> 1
    assert revenu[1].moyenne_normalisee == 0.0  # min -> 0
    assert revenu[2].moyenne_normalisee == 0.5  # milieu
    assert by_cluster[0].effectif == 6


def test_get_repartition_orders_levels_by_severity() -> None:
    repo = FakeClusterRepository(
        mailles=[FragiliteMailleAggregate("11", {"Élevée": 5, "Faible": 12, "Faible-modérée": 3})]
    )
    repartition = FragiliteService(repo).get_repartition("code_region")

    assert repartition.by == "code_region"
    niveaux = [n.niveau for n in repartition.mailles[0].repartition]
    assert niveaux == ["Faible", "Faible-modérée", "Élevée"]  # ordonné par gravité croissante


def test_get_profils_handles_missing_feature() -> None:
    # Feature absente du seed (toutes les moyennes None) -> normalisée None, pas de crash.
    repo = FakeClusterRepository(
        profils=[
            ClusterProfilAggregate(0, "c0", "Faible", 1, {"densite_pop_km2": None}),
            ClusterProfilAggregate(1, "c1", "Élevée", 1, {"densite_pop_km2": None}),
        ]
    )
    profils = FragiliteService(repo).get_profils()
    densite = next(f for f in profils[0].features if f.nom == "densite_pop_km2")
    assert densite.moyenne is None
    assert densite.moyenne_normalisee is None
