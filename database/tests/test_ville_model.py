"""Tests du modèle ORM `Ville` (table villes).

Les tests d'intégration (round-trip ORM) nécessitent un PostgreSQL accessible via
`TEST_DATABASE_URL` (défaut : la `DATABASE_URL` de la configuration). Ils sont ignorés
(skip) si la base est indisponible. Les tests de métadonnées, eux, ne requièrent aucune base."""

from sqlalchemy.orm import Session

from obrail_database.models import Ville

EXPECTED_COLUMNS = {
    "citycode", "city_name", "nom_insee", "lat_insee", "lon_insee",
    "code_dept", "code_region", "population_insee", "surface_km2",
    "densite_pop_km2", "revenu_median_uc", "taux_sans_voiture",
    "voitures_par_menage", "part_65plus", "distance_dom_trav_med_km",
    "nb_gares", "nb_trajets_total", "nb_trajets_moy_arret",
    "nb_trajets_max_arret", "nb_lignes_total", "premier_depart_matin",
    "dernier_depart_ville", "amplitude_moy_h", "amplitude_max_h",
    "amplitude_min_h", "service_weekend", "service_7j_sur_7",
    "dist_gare_min_m", "has_gare", "accessibilite_ord",
    "dernier_depart_apres_minuit",
}  # fmt: skip


def test_tablename() -> None:
    assert Ville.__tablename__ == "villes"


def test_primary_key() -> None:
    pk = [c.name for c in Ville.__table__.primary_key.columns]
    assert pk == ["citycode"]


def test_columns_match_source() -> None:
    assert set(Ville.__table__.columns.keys()) == EXPECTED_COLUMNS


def test_indexes_declared() -> None:
    indexed = {c.name for c in Ville.__table__.columns if c.index}
    assert {"city_name", "code_dept", "code_region", "has_gare"} <= indexed


def test_insert_roundtrip(session: Session) -> None:
    session.add(
        Ville(
            citycode="01004",
            city_name="Ambérieu-en-Bugey",
            code_dept="01",
            code_region="84",
            population_insee=15934.0,
            has_gare=True,
            nb_gares=2,
            accessibilite_ord=3,
        )
    )
    session.flush()  # exécute l'INSERT sans valider (rollback en teardown)

    got = session.get(Ville, "01004")
    assert got is not None
    assert got.city_name == "Ambérieu-en-Bugey"
    assert got.has_gare is True
    assert got.nb_gares == 2
