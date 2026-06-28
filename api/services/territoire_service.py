"""Cas d'usage de l'onglet « Territoires & couverture ferroviaire »."""

from repositories.interfaces import TerritoireRepository
from schemas.liaison import GeoPoint
from schemas.territoire import (
    AmplitudeBin,
    AmplitudeDistribution,
    Couverture,
    CouvertureMaille,
    VilleGeoPoint,
)


class TerritoireService:
    """Construit les données territoriales à partir du repository."""

    def __init__(self, repository: TerritoireRepository) -> None:
        self._repository = repository

    def get_carte(
        self,
        dimension: str,
        code_dept: str | None = None,
        code_region: str | None = None,
        has_gare: bool | None = None,
    ) -> list[VilleGeoPoint]:
        """V6.1 - communes géolocalisées et la valeur de la dimension cartographiée."""
        return [
            VilleGeoPoint(
                citycode=v.citycode,
                city_name=v.city_name,
                geo=GeoPoint(lat=v.lat, lon=v.lon),
                population=v.population,
                valeur=v.valeur,
                has_gare=v.has_gare,
            )
            for v in self._repository.villes_carte(dimension, code_dept, code_region, has_gare)
        ]

    def get_couverture(self, by: str) -> Couverture:
        """V6.2 - couverture ferroviaire agrégée par maille (département ou région)."""
        return Couverture(
            by=by,
            mailles=[
                CouvertureMaille(
                    cle=m.cle,
                    nb_communes=m.nb_communes,
                    taux_avec_gare=m.taux_avec_gare,
                    nb_trajets_total=m.nb_trajets_total,
                    accessibilite_moy=m.accessibilite_moy,
                )
                for m in self._repository.couverture(by)
            ],
        )

    def get_amplitude(self, bin_h: float = 1.0) -> AmplitudeDistribution:
        """V6.4 - distribution de l'amplitude de service + part desservie après minuit."""
        agg = self._repository.amplitude(bin_h)
        return AmplitudeDistribution(
            bin_h=bin_h,
            part_apres_minuit=agg.part_apres_minuit,
            bins=[
                AmplitudeBin(min_h=b.min_h, max_h=b.max_h, nb_communes=b.nb_communes)
                for b in agg.bins
            ],
        )
