"""Cas d'usage de l'onglet « Empreinte carbone » (train vs avion)."""

from repositories.interfaces import CarbonRepository
from schemas.carbon import Co2Tranche, ComparaisonAvion, ScatterBin, ScatterDensity

_GRAMMES_PAR_TONNE = 1_000_000

# Facteur d'émission moyen de l'avion court/moyen-courrier (gCO2e par voyageur-km),
# ordre de grandeur ADEME / EEA pour les vols intra-européens (avec forçage radiatif).
# Paramètre exogène, surchargeable par requête et affiché côté UI (transparence méthodo).
_DEFAULT_AVION_G_PAR_PKM = 230.0


class CarbonService:
    """Construit les indicateurs carbone à partir des agrégats des vues."""

    def __init__(self, repository: CarbonRepository) -> None:
        self._repository = repository

    def get_comparaison(self, facteur_avion_g_par_pkm: float | None = None) -> ComparaisonAvion:
        """CO₂ évité : émissions avion estimées − émissions réelles du train.

        L'estimation avion applique le facteur (g/pkm) aux voyageur-km parcourus en
        train, tranche de distance par tranche de distance.
        """
        facteur = facteur_avion_g_par_pkm or _DEFAULT_AVION_G_PAR_PKM
        tranches: list[Co2Tranche] = []
        train_total_g = 0.0
        avion_total_g = 0.0
        for band in self._repository.comparaison_bands():
            avion_g = facteur * band.train_pkm
            train_total_g += band.train_emissions_g
            avion_total_g += avion_g
            tranches.append(
                Co2Tranche(
                    min_km=band.min_km,
                    max_km=band.max_km,
                    train_t=band.train_emissions_g / _GRAMMES_PAR_TONNE,
                    avion_t=avion_g / _GRAMMES_PAR_TONNE,
                )
            )
        return ComparaisonAvion(
            facteur_avion_g_par_pkm=facteur,
            co2_train_total_t=train_total_g / _GRAMMES_PAR_TONNE,
            co2_avion_estime_t=avion_total_g / _GRAMMES_PAR_TONNE,
            co2_evite_t=(avion_total_g - train_total_g) / _GRAMMES_PAR_TONNE,
            par_tranche=tranches,
        )

    def get_density(self) -> ScatterDensity:
        """V5.2 — densité distance × intensité carbone, précalculée et colorée par mode."""
        return ScatterDensity(
            bins=[
                ScatterBin(
                    x_km=cell.x_km,
                    y_co2_pkm=cell.y_co2_pkm,
                    mode=cell.mode,
                    count=cell.count,
                )
                for cell in self._repository.carbon_density()
            ]
        )
