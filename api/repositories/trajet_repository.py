"""Implémentation SQLAlchemy de `TrajetRepository`."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import LiaisonAggregate

# Lecture de la vue matérialisée des liaisons (cf. etl/views.py).
_LIAISONS_SQL = text("""
SELECT dep_city, dep_lat, dep_lon, arr_city, arr_lat, arr_lon,
       nb_trajets, nb_nuit, distance_moy_km, co2_moy_par_pkm
FROM mv_liaisons
ORDER BY nb_trajets DESC
LIMIT :limit
""")


class SqlAlchemyTrajetRepository:
    """Accès aux trajets via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def top_liaisons(self, limit: int) -> list[LiaisonAggregate]:
        rows = self._session.execute(_LIAISONS_SQL, {"limit": limit}).mappings().all()
        return [
            LiaisonAggregate(
                departure_city=row["dep_city"],
                departure_lat=row["dep_lat"],
                departure_lon=row["dep_lon"],
                arrival_city=row["arr_city"],
                arrival_lat=row["arr_lat"],
                arrival_lon=row["arr_lon"],
                nb_trajets=row["nb_trajets"],
                nb_nuit=row["nb_nuit"],
                distance_moy_km=row["distance_moy_km"],
                co2_moy_par_pkm=row["co2_moy_par_pkm"],
            )
            for row in rows
        ]
