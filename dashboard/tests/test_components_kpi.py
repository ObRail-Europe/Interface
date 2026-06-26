"""Tests du composant bandeau de KPI (fonction pure, sans API)."""

from components.kpi import kpi_band

SAMPLE = {
    "total_trajets": 15,
    "part_nuit": 0.2,
    "nb_operateurs": 4,
    "nb_villes_desservies": 12,
    "nb_pays": 3,
    "part_transfrontalier": 0.2,
    "distance_mediane_km": 425.0,
    "co2_moyen_par_pkm": 2.5,
    "emissions_co2_totales_t": 0.01,
}


def test_kpi_band_has_eight_cards() -> None:
    assert len(kpi_band(SAMPLE).children) == 8


def test_kpi_band_formats_values() -> None:
    cards = kpi_band(SAMPLE).children
    assert cards[0].children[0].children == "15"  # valeur Trajets
    assert cards[0].children[1].children == "Trajets"  # libellé
    assert cards[1].children[0].children.startswith("20")  # part de nuit en %


def test_kpi_band_handles_null_distance() -> None:
    band = kpi_band({**SAMPLE, "distance_mediane_km": None})
    distance_card = band.children[6]
    assert distance_card.children[0].children.startswith("0")  # 0 km, pas d'erreur
