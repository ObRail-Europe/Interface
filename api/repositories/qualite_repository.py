"""Implémentation SQLAlchemy de `QualiteRepository` (lecture des vues qualité)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from repositories.interfaces import (
    AnomalieAggregate,
    ColonneCompletudeAggregate,
    SourceVolumeAggregate,
)

# Lecture des vues matérialisées (audits précalculés, cf. etl/views.py).
_COMPLETUDE_SQL = text("""
SELECT colonne, nb_nuls, nb_lignes
FROM mv_qualite_completude
WHERE source_table = :table
ORDER BY nb_nuls DESC, colonne
""")

_ANOMALIES_SQL = text("""
SELECT type, libelle, nb, severite
FROM mv_qualite_anomalies
ORDER BY nb DESC, type
""")

_VOLUMETRIE_SQL = text("""
SELECT cle, nb
FROM mv_qualite_volumetrie
ORDER BY nb DESC, cle
""")


class SqlAlchemyQualiteRepository:
    """Accès aux audits qualité via une session SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def completude(self, table: str) -> list[ColonneCompletudeAggregate]:
        rows = self._session.execute(_COMPLETUDE_SQL, {"table": table}).mappings().all()
        return [
            ColonneCompletudeAggregate(
                colonne=row["colonne"], nb_nuls=row["nb_nuls"], nb_lignes=row["nb_lignes"]
            )
            for row in rows
        ]

    def anomalies(self) -> list[AnomalieAggregate]:
        rows = self._session.execute(_ANOMALIES_SQL).mappings().all()
        return [
            AnomalieAggregate(
                type=row["type"], libelle=row["libelle"], nb=row["nb"], severite=row["severite"]
            )
            for row in rows
        ]

    def volumetrie(self) -> list[SourceVolumeAggregate]:
        rows = self._session.execute(_VOLUMETRIE_SQL).mappings().all()
        return [SourceVolumeAggregate(cle=row["cle"], nb=row["nb"]) for row in rows]
