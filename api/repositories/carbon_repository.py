"""Implémentation SQLAlchemy de `CarbonRepository` (lecture des vues carbone)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import Co2BandAggregate

# Largeur des tranches de distance de mv_co2_comparaison
_BAND_KM = 50.0

# Lecture de la vue matérialisée.
_COMPARAISON_SQL = text("""
SELECT dist_min, nb_trajets, train_pkm, train_emissions_g
FROM mv_co2_comparaison
ORDER BY dist_min
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
