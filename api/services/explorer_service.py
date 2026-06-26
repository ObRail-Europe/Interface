"""Cas d'usage de l'onglet « Explorateur de trajets »."""

from repositories.interfaces import TrajetRepository
from schemas.liaison import GeoPoint, Liaison


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
