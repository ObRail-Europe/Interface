"""DTO de l'onglet « Empreinte carbone » (train vs avion)."""

from pydantic import BaseModel


class Co2Tranche(BaseModel):
    """Émissions CO₂ (tonnes) d'une tranche de distance : train réel vs estimation avion."""

    min_km: float
    max_km: float
    train_t: float
    avion_t: float


class ComparaisonAvion(BaseModel):
    """V5.1 — CO₂ évité en prenant le train plutôt que l'avion.

    Le facteur avion (gCO2e / voyageur-km) est un paramètre **exogène, documenté et
    affiché** : l'estimation avion applique ce facteur aux voyageur-km parcourus en
    train, et le CO₂ évité est l'écart avec les émissions réelles du train.
    """

    facteur_avion_g_par_pkm: float
    co2_train_total_t: float
    co2_avion_estime_t: float
    co2_evite_t: float
    par_tranche: list[Co2Tranche]
