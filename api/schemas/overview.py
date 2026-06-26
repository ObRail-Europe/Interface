"""DTO de l'onglet « Vue d'ensemble »."""

from pydantic import BaseModel, Field


class OverviewKPI(BaseModel):
    """Indicateurs-clés du réseau (bandeau de KPI, V1.1)."""

    total_trajets: int = Field(description="Nombre total de trajets")
    part_nuit: float = Field(description="Part des trains de nuit (0..1)")
    nb_operateurs: int
    nb_villes_desservies: int
    nb_pays: int
    part_transfrontalier: float = Field(description="Part des trajets transfrontaliers (0..1)")
    distance_mediane_km: float | None
    co2_moyen_par_pkm: float | None
    emissions_co2_totales_t: float = Field(description="Émissions totales en tonnes")
