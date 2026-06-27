"""Implémentation SQLAlchemy de `CarbonRepository` (lecture des vues carbone)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import (
    CarbonDensityCell,
    Co2BandAggregate,
    ModeDistributionAggregate,
)

# Largeur des tranches de distance de mv_co2_comparaison
_BAND_KM = 50.0

# Lecture des vues matérialisées (agrégats précalculés, cf. etl/views.py).
_COMPARAISON_SQL = text("""
SELECT dist_min, nb_trajets, train_pkm, train_emissions_g
FROM mv_co2_comparaison
ORDER BY dist_min
""")

_DENSITY_SQL = text("""
SELECT mode, dist_mid, co2_mid, nb_trajets
FROM mv_carbon_density
ORDER BY mode, dist_mid, co2_mid
""")

_DISTRIBUTION_SQL = text("""
SELECT mode, nb_trajets, co2_min, co2_q1, co2_median, co2_q3, co2_max, co2_moy
FROM mv_co2_distribution
ORDER BY mode
""")


class SqlAlchemyCarbonRepository:
    """Accès aux agrégats carbone via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def comparaison_bands(self) -> list[Co2BandAggregate]:
        rows = self._session.execute(_COMPARAISON_SQL).mappings().all()
        return [
            Co2BandAggregate(
                min_km=float(row["dist_min"]),
                max_km=float(row["dist_min"]) + _BAND_KM,
                nb_trajets=row["nb_trajets"],
                train_pkm=float(row["train_pkm"]),
                train_emissions_g=float(row["train_emissions_g"]),
            )
            for row in rows
        ]

    def carbon_density(self) -> list[CarbonDensityCell]:
        rows = self._session.execute(_DENSITY_SQL).mappings().all()
        return [
            CarbonDensityCell(
                mode=row["mode"],
                x_km=float(row["dist_mid"]),
                y_co2_pkm=float(row["co2_mid"]),
                count=row["nb_trajets"],
            )
            for row in rows
        ]

    def co2_distribution(self) -> list[ModeDistributionAggregate]:
        rows = self._session.execute(_DISTRIBUTION_SQL).mappings().all()
        return [
            ModeDistributionAggregate(
                mode=row["mode"],
                count=row["nb_trajets"],
                co2_min=float(row["co2_min"]),
                co2_q1=float(row["co2_q1"]),
                co2_median=float(row["co2_median"]),
                co2_q3=float(row["co2_q3"]),
                co2_max=float(row["co2_max"]),
                co2_moy=float(row["co2_moy"]),
            )
            for row in rows
        ]
