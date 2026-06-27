"""Tests unitaires du service Empreinte carbone (repository en mémoire, sans base)."""

from repositories.interfaces import CarbonDensityCell, Co2BandAggregate
from services.carbon_service import CarbonService


class FakeCarbonRepository:
    """Doublure en mémoire de `CarbonRepository`."""

    def __init__(
        self,
        bands: list[Co2BandAggregate] | None = None,
        density: list[CarbonDensityCell] | None = None,
    ) -> None:
        self._bands = bands or []
        self._density = density or []

    def comparaison_bands(self) -> list[Co2BandAggregate]:
        return self._bands

    def carbon_density(self) -> list[CarbonDensityCell]:
        return self._density


def test_get_comparaison_applies_factor_and_totals() -> None:
    # Deux tranches ; 1 000 000 pkm cumulés, 2 t réelles en train.
    repo = FakeCarbonRepository(
        [
            Co2BandAggregate(0.0, 100.0, 4, 400_000.0, 800_000.0),  # 0.8 t train
            Co2BandAggregate(100.0, 200.0, 6, 600_000.0, 1_200_000.0),  # 1.2 t train
        ]
    )
    comp = CarbonService(repo).get_comparaison(facteur_avion_g_par_pkm=200.0)

    # Avion estimé : 200 g/pkm × 1 000 000 pkm = 200 000 000 g = 200 t.
    assert comp.facteur_avion_g_par_pkm == 200.0
    assert comp.co2_train_total_t == 2.0
    assert comp.co2_avion_estime_t == 200.0
    assert comp.co2_evite_t == 198.0
    assert len(comp.par_tranche) == 2
    assert comp.par_tranche[0].avion_t == 80.0  # 200 × 400000 / 1e6
    assert comp.par_tranche[0].train_t == 0.8


def test_get_comparaison_uses_documented_default_factor() -> None:
    repo = FakeCarbonRepository([Co2BandAggregate(0.0, 100.0, 1, 1000.0, 100.0)])
    comp = CarbonService(repo).get_comparaison()  # aucun facteur fourni

    assert comp.facteur_avion_g_par_pkm == 230.0  # défaut documenté
    assert comp.co2_avion_estime_t > comp.co2_train_total_t


def test_get_density_maps_cells_per_mode() -> None:
    repo = FakeCarbonRepository(
        density=[
            CarbonDensityCell(mode="train", x_km=0.0, y_co2_pkm=20.0, count=8),
            CarbonDensityCell(mode="flight", x_km=650.0, y_co2_pkm=250.0, count=3),
        ]
    )
    density = CarbonService(repo).get_density()

    assert len(density.bins) == 2
    assert {b.mode for b in density.bins} == {"train", "flight"}
    train = next(b for b in density.bins if b.mode == "train")
    assert train.x_km == 0.0 and train.y_co2_pkm == 20.0 and train.count == 8
