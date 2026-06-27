"""Implémentation SQLAlchemy de `TrajetRepository`."""

from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session

from models import Trajet
from repositories.interfaces import DistanceBinAggregate, LiaisonAggregate, TrajetFilter

# Re-regroupe les bins de 25 km de mv_distance_hist selon le pas demandé.
_DISTANCE_HIST_SQL = text("""
SELECT floor(bin_min / :bin) * :bin AS min_km,
       floor(bin_min / :bin) * :bin + :bin AS max_km,
       sum(count_jour)::bigint AS count_jour,
       sum(count_nuit)::bigint AS count_nuit
FROM mv_distance_hist
GROUP BY 1, 2
ORDER BY min_km
""")

# Lecture de la vue matérialisée des liaisons (cf. etl/views.py).
_LIAISONS_SQL = text("""
SELECT dep_city, dep_lat, dep_lon, arr_city, arr_lat, arr_lon,
       nb_trajets, nb_nuit, distance_moy_km, co2_moy_par_pkm
FROM mv_liaisons
ORDER BY nb_trajets DESC
LIMIT :limit
""")

# Colonnes de tri autorisées (liste blanche).
_SORT_COLUMNS = {
    "id": Trajet.id,
    "distance_km": Trajet.distance_km,
    "departure_time": Trajet.departure_time,
    "departure_city": Trajet.departure_city,
    "arrival_city": Trajet.arrival_city,
    "agency_name": Trajet.agency_name,
    "co2_per_pkm": Trajet.co2_per_pkm,
}


def _apply_filters(stmt: Select, criteria: TrajetFilter) -> Select:
    """Ajoute les clauses WHERE selon les critères fournis (s'appuie sur les index)."""
    if criteria.mode:
        stmt = stmt.where(Trajet.mode == criteria.mode)
    if criteria.is_night is not None:
        stmt = stmt.where(Trajet.is_night_train == criteria.is_night)
    if criteria.departure_city:
        stmt = stmt.where(Trajet.departure_city == criteria.departure_city)
    if criteria.arrival_city:
        stmt = stmt.where(Trajet.arrival_city == criteria.arrival_city)
    if criteria.agency_name:
        stmt = stmt.where(Trajet.agency_name == criteria.agency_name)
    if criteria.departure_country:
        stmt = stmt.where(Trajet.departure_country == criteria.departure_country)
    if criteria.arrival_country:
        stmt = stmt.where(Trajet.arrival_country == criteria.arrival_country)
    if criteria.distance_min_km is not None:
        stmt = stmt.where(Trajet.distance_km >= criteria.distance_min_km)
    if criteria.distance_max_km is not None:
        stmt = stmt.where(Trajet.distance_km <= criteria.distance_max_km)
    return stmt


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

    def list_trajets(
        self,
        criteria: TrajetFilter,
        sort_field: str,
        sort_desc: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Trajet], int]:
        stmt = _apply_filters(select(Trajet), criteria)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        column = _SORT_COLUMNS.get(sort_field, Trajet.id)
        stmt = stmt.order_by(column.desc() if sort_desc else column.asc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        return list(self._session.scalars(stmt).all()), total

    def distance_histogram(self, bin_km: int) -> list[DistanceBinAggregate]:
        rows = self._session.execute(_DISTANCE_HIST_SQL, {"bin": bin_km}).mappings().all()
        return [
            DistanceBinAggregate(
                min_km=row["min_km"],
                max_km=row["max_km"],
                count_jour=row["count_jour"],
                count_nuit=row["count_nuit"],
            )
            for row in rows
        ]
