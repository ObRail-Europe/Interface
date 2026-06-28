"""Modèle ORM de la table `clusters` (source : clusters_final.csv).

Issu du modèle de clustering `cluster_fragilite.joblib`.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from obrail_database.models.base import Base


class Cluster(Base):
    """Affectation d'une commune à un cluster de fragilité + features socio-mobilité."""

    __tablename__ = "clusters"

    row_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    city_name: Mapped[str] = mapped_column(String, index=True)
    # Rattachement à `villes`, résolu par coordonnées lors de l'ETL (voir etl/resolve.py).
    citycode: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("villes.citycode"), index=True
    )
    lat_insee: Mapped[float | None]
    lon_insee: Mapped[float | None]
    cluster: Mapped[int] = mapped_column(index=True)
    cluster_nom: Mapped[str | None] = mapped_column(String)
    niveau_fragilite: Mapped[str | None] = mapped_column(String, index=True)
    has_gare: Mapped[bool | None]
    accessibilite_ord: Mapped[int | None]
    dist_gare_min_m: Mapped[float | None]
    nb_trajets_total: Mapped[float | None]
    nb_lignes_total: Mapped[float | None]
    amplitude_moy_h: Mapped[float | None]
    revenu_median_uc: Mapped[float | None]
    voitures_par_menage: Mapped[float | None]
    taux_sans_voiture: Mapped[float | None]
    part_65plus: Mapped[float | None]
    distance_dom_trav_med_km: Mapped[float | None]
    population: Mapped[float | None]
    densite_pop_km2: Mapped[float | None]

    def __repr__(self) -> str:
        return f"<Cluster row_id={self.row_id} {self.city_name!r} cluster={self.cluster}>"
