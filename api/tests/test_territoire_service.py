"""Tests unitaires du service Territoires (repository en mémoire, sans base)."""

from repositories.interfaces import (
    AmplitudeAggregate,
    AmplitudeBinAggregate,
    CouvertureMailleAggregate,
    VilleGeoAggregate,
)
from services.territoire_service import TerritoireService


class FakeTerritoireRepository:
    """Doublure en mémoire de `TerritoireRepository`."""

    def __init__(
        self,
        villes: list[VilleGeoAggregate] | None = None,
        mailles: list[CouvertureMailleAggregate] | None = None,
        amplitude: AmplitudeAggregate | None = None,
    ) -> None:
        self._villes = villes or []
        self._mailles = mailles or []
        self._amplitude = amplitude or AmplitudeAggregate(bins=[], part_apres_minuit=0.0)
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

    def couverture(self, by: str) -> list[CouvertureMailleAggregate]:
        self.last_call = {"by": by}
        return self._mailles

    def amplitude(self, bin_h: float) -> AmplitudeAggregate:
        self.last_call = {"bin_h": bin_h}
        return self._amplitude


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


def test_get_couverture_maps_mailles() -> None:
    repo = FakeTerritoireRepository(mailles=[CouvertureMailleAggregate("75", 1, 1.0, 331694, 3.0)])
    couverture = TerritoireService(repo).get_couverture("code_dept")

    assert couverture.by == "code_dept"
    assert len(couverture.mailles) == 1
    assert couverture.mailles[0].cle == "75"
    assert couverture.mailles[0].taux_avec_gare == 1.0
    assert repo.last_call == {"by": "code_dept"}


def test_get_amplitude_maps_bins_and_part() -> None:
    repo = FakeTerritoireRepository(
        amplitude=AmplitudeAggregate(
            bins=[AmplitudeBinAggregate(16.0, 17.0, 3), AmplitudeBinAggregate(17.0, 18.0, 5)],
            part_apres_minuit=0.42,
        )
    )
    dist = TerritoireService(repo).get_amplitude(bin_h=1.0)

    assert dist.bin_h == 1.0
    assert dist.part_apres_minuit == 0.42
    assert [b.nb_communes for b in dist.bins] == [3, 5]
    assert repo.last_call == {"bin_h": 1.0}
