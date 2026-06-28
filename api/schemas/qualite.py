"""DTO de l'onglet « Qualité des données » (V8)."""

from pydantic import BaseModel


class ColonneCompletude(BaseModel):
    """Complétude d'une colonne (V8.1)."""

    nom: str
    taux_complet: float  # 0..1
    nb_nuls: int


class Completude(BaseModel):
    """V8.1 — complétude par colonne pour une table."""

    table: str
    nb_lignes: int
    colonnes: list[ColonneCompletude]


class Anomalie(BaseModel):
    """V8.2 — un type d'anomalie et son effectif."""

    type: str
    libelle: str
    nb: int
    severite: str  # info | warn | error


class Anomalies(BaseModel):
    """V8.2 — anomalies & doublons."""

    anomalies: list[Anomalie]


class SourceVolume(BaseModel):
    """V8.4 — volume de trajets d'une source."""

    cle: str
    nb: int


class Volumetrie(BaseModel):
    """V8.4 — volumétrie par source."""

    sources: list[SourceVolume]
