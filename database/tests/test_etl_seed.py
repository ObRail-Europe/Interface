"""Test d'intégration de bout en bout sur le jeu de données seed (fixtures/*.csv)."""

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from obrail_database.models import Cluster, Trajet, Ville


def test_seed_counts(seeded_session: Session) -> None:
    s = seeded_session
    assert s.scalar(select(func.count()).select_from(Ville)) == 12
    assert s.scalar(select(func.count()).select_from(Cluster)) == 8
    assert s.scalar(select(func.count()).select_from(Trajet)) == 15


def test_seed_resolution(seeded_session: Session) -> None:
    s = seeded_session
    clusters_resolus = s.scalar(
        select(func.count()).select_from(Cluster).where(Cluster.citycode.isnot(None))
    )
    depart_resolus = s.scalar(
        select(func.count()).select_from(Trajet).where(Trajet.departure_citycode.isnot(None))
    )
    arrivee_resolus = s.scalar(
        select(func.count()).select_from(Trajet).where(Trajet.arrival_citycode.isnot(None))
    )
    assert clusters_resolus == 7  # « Nulle Part » (coords hors villes) non rattaché
    assert depart_resolus == 15  # tous les départs sont des villes FR du référentiel
    assert arrivee_resolus == 11  # Berlin / Frankfurt / Milano / Nice non résolus


def test_seed_jour_nuit(seeded_session: Session) -> None:
    nuit = seeded_session.scalar(
        select(func.count()).select_from(Trajet).where(Trajet.is_night_train.is_(True))
    )
    assert nuit == 3


def test_seed_join_trajets_villes(seeded_session: Session) -> None:
    # La jointure trajets → villes via citycode résolu est exploitable (incl. alias Paris).
    top = seeded_session.execute(
        text(
            "SELECT v.city_name, count(*) AS n "
            "FROM trajets t JOIN villes v ON v.citycode = t.departure_citycode "
            "GROUP BY v.city_name ORDER BY n DESC, v.city_name LIMIT 1"
        )
    ).one()
    assert top.city_name == "Paris"  # « Paris 09 Opera » est rattaché à Paris via l'alias
