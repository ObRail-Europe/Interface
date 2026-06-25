"""Tests du modèle ORM `Cluster` (table clusters)."""

from sqlalchemy.orm import Session

from models import Cluster

EXPECTED_COLUMNS = {
    "row_id", "city_name", "lat_insee", "lon_insee", "cluster", "cluster_nom",
    "niveau_fragilite", "has_gare", "accessibilite_ord", "dist_gare_min_m",
    "nb_trajets_total", "nb_lignes_total", "amplitude_moy_h", "revenu_median_uc",
    "voitures_par_menage", "taux_sans_voiture", "part_65plus",
    "distance_dom_trav_med_km", "population", "densite_pop_km2", "citycode",
}  # fmt: skip


def test_tablename() -> None:
    assert Cluster.__tablename__ == "clusters"


def test_primary_key() -> None:
    pk = [c.name for c in Cluster.__table__.primary_key.columns]
    assert pk == ["row_id"]


def test_columns_match_source() -> None:
    assert set(Cluster.__table__.columns.keys()) == EXPECTED_COLUMNS


def test_indexes_declared() -> None:
    indexed = {c.name for c in Cluster.__table__.columns if c.index}
    assert {"city_name", "cluster", "niveau_fragilite", "citycode"} <= indexed


def test_insert_roundtrip(session: Session) -> None:
    session.add(
        Cluster(
            row_id=8591,
            city_name="Abbeville",
            cluster=0,
            cluster_nom="c0 - Gare, pôle urbain dense",
            niveau_fragilite="Faible",
            has_gare=True,
            accessibilite_ord=3,
            population=22395.0,
        )
    )
    session.flush()  # exécute l'INSERT sans valider (rollback en teardown)

    got = session.get(Cluster, 8591)
    assert got is not None
    assert got.city_name == "Abbeville"
    assert got.niveau_fragilite == "Faible"
    assert got.cluster == 0
