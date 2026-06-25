"""DTO d'un opérateur (V1.4)."""

from pydantic import BaseModel


class OperateurStat(BaseModel):
    agency_name: str
    nb_trajets: int
    part_nuit: float  # 0..1
