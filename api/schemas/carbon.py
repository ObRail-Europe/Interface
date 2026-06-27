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


class ScatterBin(BaseModel):
    """Cellule de densité (distance × intensité carbone) pour un mode."""

    x_km: float  # centre du bin de distance
    y_co2_pkm: float  # centre du bin d'intensité (g/pkm)
    mode: str
    count: int


class ScatterDensity(BaseModel):
    """V5.2 — densité distance × intensité carbone (agrégée, colorée par mode)."""

    bins: list[ScatterBin]


class ModeDistribution(BaseModel):
    """Résumé statistique du CO₂/pkm d'un mode (box plot : quartiles + extrêmes)."""

    mode: str
    count: int
    min: float
    q1: float
    mediane: float
    q3: float
    max: float
    moyenne: float


class Co2ParMode(BaseModel):
    """V5.3 — distribution du CO₂/pkm par mode (train vs avion)."""

    modes: list[ModeDistribution]
