"""Tests unitaires du service Explorateur (repository en mémoire, sans base)."""

from types import SimpleNamespace
from typing import Any

from repositories.interfaces import LiaisonAggregate, TrajetFilter
from schemas.trajet import TripFilter
from services.explorer_service import ExplorerService


class FakeTrajetRepository:
    """Doublure en mémoire de `TrajetRepository`."""

    def __init__(
        self,
        liaisons: list[LiaisonAggregate] | None = None,
        rows: list[Any] | None = None,
        total: int = 0,
    ) -> None:
        self._liaisons = liaisons or []
        self._rows = rows or []
        self._total = total

    def top_liaisons(self, limit: int) -> list[LiaisonAggregate]:
        return self._liaisons[:limit]

    def list_trajets(
        self, criteria: TrajetFilter, sort_field: str, sort_desc: bool, page: int, page_size: int
    ) -> tuple[list[Any], int]:
        return self._rows, self._total


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


def test_list_trajets_builds_page() -> None:
    row = SimpleNamespace(
        id=1,
        trip_id="T1",
        mode="train",
        agency_name="SNCF",
        route_short_name=None,
        departure_city="Paris",
        departure_country="FR",
        arrival_city="Lyon",
        arrival_country="FR",
        departure_time="07:00:00",
        arrival_time="09:00:00",
        distance_km=425.0,
        is_night_train=False,
        emissions_co2=1000.0,
        co2_per_pkm=2.4,
    )
    repo = FakeTrajetRepository(rows=[row], total=42)
    page = ExplorerService(repo).list_trajets(
        TripFilter(), sort="-distance_km", page=2, page_size=20
    )

    assert page.total == 42
    assert page.pages == 3  # ceil(42 / 20)
    assert page.page == 2
    assert page.items[0].departure_city == "Paris"
