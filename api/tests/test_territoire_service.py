"""Tests unitaires du service Territoires (repository en mémoire, sans base)."""

from repositories.interfaces import VilleGeoAggregate
from services.territoire_service import TerritoireService


class FakeTerritoireRepository:
    """Doublure en mémoire de `TerritoireRepository`."""

    def __init__(self, villes: list[VilleGeoAggregate] | None = None) -> None:
        self._villes = villes or []
        self.last_call: dict[str, object] = {}

    def villes_carte(
        self,
        dimension: str,
        code_dept: str | None,
        code_region: str | None,
        has_gare: bool | None,
    ) -> list[VilleGeoAggregate]:
        self.last_call = {
            "dimension": dimension,
            "code_dept": code_dept,
            "code_region": code_region,
            "has_gare": has_gare,
        }
        return self._villes


def test_get_carte_maps_to_geo_points() -> None:
    repo = FakeTerritoireRepository(
        [VilleGeoAggregate("75056", "Paris", 48.85, 2.35, 2103778.0, 331694.0, True)]
    )
    points = TerritoireService(repo).get_carte("nb_trajets_total", code_dept="75")

    assert len(points) == 1
    assert points[0].geo.lat == 48.85 and points[0].geo.lon == 2.35
    assert points[0].valeur == 331694.0
    assert points[0].has_gare is True
    assert repo.last_call == {
        "dimension": "nb_trajets_total",
        "code_dept": "75",
        "code_region": None,
        "has_gare": None,
    }
