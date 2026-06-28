"""DTO de l'onglet « Territoires & couverture ferroviaire » (V6)."""

from pydantic import BaseModel

from schemas.liaison import GeoPoint


class VilleGeoPoint(BaseModel):
    """V6.1 - commune géolocalisée et la valeur de la dimension cartographiée."""

    citycode: str
    city_name: str
    geo: GeoPoint
    population: float | None
    valeur: float | None  # valeur de la dimension demandée (gare, accessibilité, trajets…)
    has_gare: bool | None


class CouvertureMaille(BaseModel):
    """Couverture agrégée d'une maille (département ou région)."""

    cle: str
    nb_communes: int
    taux_avec_gare: float  # 0..1
    nb_trajets_total: int
    accessibilite_moy: float | None


class Couverture(BaseModel):
    """V6.2 - couverture ferroviaire par maille territoriale."""

    by: str  # "code_dept" | "code_region"
    mailles: list[CouvertureMaille]


class AmplitudeBin(BaseModel):
    """Tranche d'amplitude de service (heures) et nombre de communes concernées."""

    min_h: float
    max_h: float
    nb_communes: int


class AmplitudeDistribution(BaseModel):
    """V6.4 - distribution de l'amplitude de service + part desservie après minuit."""

    bin_h: float
    part_apres_minuit: float  # 0..1
    bins: list[AmplitudeBin]
