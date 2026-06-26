"""Tests unitaires du service Explorateur (repository en mémoire, sans base)."""

from repositories.interfaces import LiaisonAggregate
from services.explorer_service import ExplorerService


class FakeTrajetRepository:
    """Doublure en mémoire de `TrajetRepository`."""

    def __init__(self, liaisons: list[LiaisonAggregate] | None = None) -> None:
        self._liaisons = liaisons or []

    def top_liaisons(self, limit: int) -> list[LiaisonAggregate]:
        return self._liaisons[:limit]


def test_get_liaisons_maps_and_computes_part_nuit() -> None:
    repo = FakeTrajetRepository(
        liaisons=[
            LiaisonAggregate(
                departure_city="Paris",
                departure_lat=48.85,
                departure_lon=2.35,
                arrival_city="Lyon",
                arrival_lat=45.76,
                arrival_lon=4.84,
                nb_trajets=10,
                nb_nuit=3,
                distance_moy_km=425.0,
                co2_moy_par_pkm=2.4,
            )
        ]
    )
    result = ExplorerService(repo).get_liaisons(limit=5)

    assert len(result) == 1
    assert result[0].departure.lat == 48.85
    assert result[0].arrival_city == "Lyon"
    assert result[0].part_nuit == 0.3
