"""Modèle ORM de la table `villes` (source : villes_enriched.csv)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Ville(Base):
    """Commune française enrichie : desserte ferroviaire + indicateurs socio-économiques."""

    __tablename__ = "villes"

    citycode: Mapped[str] = mapped_column(String(10), primary_key=True)  # code INSEE
    city_name: Mapped[str] = mapped_column(String, index=True)
    nom_insee: Mapped[str | None] = mapped_column(String)
    lat_insee: Mapped[float | None]
    lon_insee: Mapped[float | None]
    code_dept: Mapped[str | None] = mapped_column(String(3), index=True)
    code_region: Mapped[str | None] = mapped_column(String(3), index=True)
    population_insee: Mapped[float | None]
    surface_km2: Mapped[float | None]
    densite_pop_km2: Mapped[float | None]
    revenu_median_uc: Mapped[float | None]
    taux_sans_voiture: Mapped[float | None]
    voitures_par_menage: Mapped[float | None]
    part_65plus: Mapped[float | None]
    distance_dom_trav_med_km: Mapped[float | None]
    nb_gares: Mapped[int | None]
    nb_trajets_total: Mapped[int | None]
    nb_trajets_moy_arret: Mapped[float | None]
    nb_trajets_max_arret: Mapped[int | None]
    nb_lignes_total: Mapped[int | None]
    # Heures au format GTFS (peuvent dépasser 24h, ex. "24:29:00") → stockées en texte.
    premier_depart_matin: Mapped[str | None] = mapped_column(String(8))
    dernier_depart_ville: Mapped[str | None] = mapped_column(String(8))
    amplitude_moy_h: Mapped[float | None]
    amplitude_max_h: Mapped[float | None]
    amplitude_min_h: Mapped[float | None]
    service_weekend: Mapped[bool | None]
    service_7j_sur_7: Mapped[bool | None]
    dist_gare_min_m: Mapped[float | None]
    has_gare: Mapped[bool | None] = mapped_column(index=True)
    accessibilite_ord: Mapped[int | None]
    dernier_depart_apres_minuit: Mapped[bool | None]

    def __repr__(self) -> str:
        return f"<Ville {self.citycode} {self.city_name!r}>"
