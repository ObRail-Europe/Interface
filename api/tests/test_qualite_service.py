"""Tests unitaires du service Qualité (repository en mémoire, sans base)."""

from repositories.interfaces import (
    AnomalieAggregate,
    ColonneCompletudeAggregate,
    SourceVolumeAggregate,
)
from services.qualite_service import QualiteService


class FakeQualiteRepository:
    """Doublure en mémoire de `QualiteRepository`."""

    def __init__(
        self,
        completude: list[ColonneCompletudeAggregate] | None = None,
        anomalies: list[AnomalieAggregate] | None = None,
        volumetrie: list[SourceVolumeAggregate] | None = None,
    ) -> None:
        self._completude = completude or []
        self._anomalies = anomalies or []
        self._volumetrie = volumetrie or []

    def completude(self, table: str) -> list[ColonneCompletudeAggregate]:
        return self._completude

    def anomalies(self) -> list[AnomalieAggregate]:
        return self._anomalies

    def volumetrie(self) -> list[SourceVolumeAggregate]:
        return self._volumetrie


def test_get_completude_computes_rate() -> None:
    repo = FakeQualiteRepository(
        completude=[
            ColonneCompletudeAggregate("id", 0, 100),
            ColonneCompletudeAggregate("arrival_citycode", 25, 100),
        ]
    )
    completude = QualiteService(repo).get_completude("trajets")

    assert completude.table == "trajets"
    assert completude.nb_lignes == 100
    by_col = {c.nom: c for c in completude.colonnes}
    assert by_col["id"].taux_complet == 1.0
    assert by_col["arrival_citycode"].taux_complet == 0.75


def test_get_completude_empty_table_does_not_divide_by_zero() -> None:
    completude = QualiteService(FakeQualiteRepository()).get_completude("villes")
    assert completude.nb_lignes == 0
    assert completude.colonnes == []


def test_get_anomalies_and_volumetrie_map() -> None:
    repo = FakeQualiteRepository(
        anomalies=[AnomalieAggregate("dup", "Doublons", 3, "warn")],
        volumetrie=[SourceVolumeAggregate("SNCF", 11), SourceVolumeAggregate("DB", 1)],
    )
    service = QualiteService(repo)
    assert service.get_anomalies().anomalies[0].severite == "warn"
    sources = service.get_volumetrie().sources
    assert [s.cle for s in sources] == ["SNCF", "DB"]
