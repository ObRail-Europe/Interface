"""DTO de l'histogramme des distances (V2.3)."""

from pydantic import BaseModel


class DistanceBin(BaseModel):
    min_km: float
    max_km: float
    count_jour: int
    count_nuit: int


class DistanceHistogram(BaseModel):
    bin_km: int  # pas effectif
    bins: list[DistanceBin]
