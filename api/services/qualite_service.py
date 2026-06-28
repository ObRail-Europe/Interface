"""Cas d'usage de l'onglet « Qualité des données »."""

from repositories.interfaces import QualiteRepository
from schemas.qualite import (
    Anomalie,
    Anomalies,
    ColonneCompletude,
    Completude,
    SourceVolume,
    Volumetrie,
)


def _taux_complet(nb_nuls: int, nb_lignes: int) -> float:
    return (nb_lignes - nb_nuls) / nb_lignes if nb_lignes else 1.0


class QualiteService:
    """Construit les indicateurs qualité à partir des agrégats des vues."""

    def __init__(self, repository: QualiteRepository) -> None:
        self._repository = repository

    def get_completude(self, table: str) -> Completude:
        """V8.1 — complétude par colonne (taux dérivé des NULLs précalculés)."""
        rows = self._repository.completude(table)
        nb_lignes = rows[0].nb_lignes if rows else 0
        return Completude(
            table=table,
            nb_lignes=nb_lignes,
            colonnes=[
                ColonneCompletude(
                    nom=row.colonne,
                    taux_complet=_taux_complet(row.nb_nuls, row.nb_lignes),
                    nb_nuls=row.nb_nuls,
                )
                for row in rows
            ],
        )

    def get_anomalies(self) -> Anomalies:
        """V8.2 — anomalies & doublons."""
        return Anomalies(
            anomalies=[
                Anomalie(type=a.type, libelle=a.libelle, nb=a.nb, severite=a.severite)
                for a in self._repository.anomalies()
            ]
        )

    def get_volumetrie(self) -> Volumetrie:
        """V8.4 — volumétrie par source."""
        return Volumetrie(
            sources=[SourceVolume(cle=s.cle, nb=s.nb) for s in self._repository.volumetrie()]
        )
