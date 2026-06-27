"""Tests des composants de l'onglet Empreinte carbone (fonctions pures, sans API)."""

from components.carbon import _THIN_SPACE, co2_counter

_COMPARAISON = {
    "facteur_avion_g_par_pkm": 230.0,
    "co2_train_total_t": 5.0,
    "co2_avion_estime_t": 55.0,
    "co2_evite_t": 50.0,
    "par_tranche": [
        {"min_km": 0.0, "max_km": 50.0, "train_t": 2.0, "avion_t": 25.0},
        {"min_km": 50.0, "max_km": 100.0, "train_t": 3.0, "avion_t": 30.0},
    ],
}


def test_co2_counter_has_hero_card_with_avoided_co2() -> None:
    band = co2_counter(_COMPARAISON)
    hero = band.children[0]
    assert "kpi-hero" in hero.className
    assert hero.children[0].children.startswith("50.0")  # 50 t évitées
    assert hero.children[1].children == "CO₂ évité vs avion"


def test_co2_counter_displays_factor_for_transparency() -> None:
    text = str(co2_counter(_COMPARAISON))
    assert f"230{_THIN_SPACE}g/pkm" in text  # facteur avion affiché
