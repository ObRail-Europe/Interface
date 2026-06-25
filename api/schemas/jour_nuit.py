"""DTO de la répartition jour / nuit (V1.2)."""

from pydantic import BaseModel


class SegmentStat(BaseModel):
    nb_trajets: int
    part: float  # 0..1


class JourNuitSplit(BaseModel):
    jour: SegmentStat
    nuit: SegmentStat
