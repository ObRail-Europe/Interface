"""Cas d'usage de l'onglet « Explorateur de trajets »."""

import math

from repositories.interfaces import TrajetFilter, TrajetRepository
from schemas.distance import DistanceBin, DistanceHistogram
from schemas.liaison import GeoPoint, Liaison
from schemas.trajet import TrajetDetail, TrajetListItem, TrajetPage, TripFilter

# défault des bins de mv_distance_hist
_BASE_BIN_KM = 25


def _ratio(part: int, total: int) -> float:
    return part / total if total else 0.0


class ExplorerService:
    """Construit les données de l'explorateur à partir du repository."""

    def __init__(self, repository: TrajetRepository) -> None:
        self._repository = repository

    def get_liaisons(self, limit: int = 100) -> list[Liaison]:
        return [
            Liaison(
                departure_city=liaison.departure_city,
                departure=GeoPoint(lat=liaison.departure_lat, lon=liaison.departure_lon),
                arrival_city=liaison.arrival_city,
                arrival=GeoPoint(lat=liaison.arrival_lat, lon=liaison.arrival_lon),
                nb_trajets=liaison.nb_trajets,
                part_nuit=_ratio(liaison.nb_nuit, liaison.nb_trajets),
                distance_moy_km=liaison.distance_moy_km,
                co2_moy_par_pkm=liaison.co2_moy_par_pkm,
            )
            for liaison in self._repository.top_liaisons(limit)
        ]

    def list_trajets(
        self, trip_filter: TripFilter, sort: str, page: int, page_size: int
    ) -> TrajetPage:
        sort_desc = sort.startswith("-")
        sort_field = sort.lstrip("-") or "id"
        criteria = TrajetFilter(**trip_filter.model_dump())
        rows, total = self._repository.list_trajets(
            criteria, sort_field, sort_desc, page, page_size
        )
        pages = math.ceil(total / page_size) if page_size else 0
        return TrajetPage(
            items=[TrajetListItem.model_validate(row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_trajet(self, trajet_id: int) -> TrajetDetail | None:
        trajet = self._repository.get_trajet(trajet_id)
        return TrajetDetail.model_validate(trajet) if trajet is not None else None

    def get_distance_histogram(self, bin_km: int = 100) -> DistanceHistogram:
        effective = max(_BASE_BIN_KM, (bin_km // _BASE_BIN_KM) * _BASE_BIN_KM)
        bins = self._repository.distance_histogram(effective)
        return DistanceHistogram(
            bin_km=effective,
            bins=[
                DistanceBin(
                    min_km=b.min_km,
                    max_km=b.max_km,
                    count_jour=b.count_jour,
                    count_nuit=b.count_nuit,
                )
                for b in bins
            ],
        )
