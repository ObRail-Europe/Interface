"""Tests des vues matérialisées de l'onglet Vue d'ensemble."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

EXPECTED_VIEWS = {"mv_overview_kpi", "mv_operateurs", "mv_departs"}


def test_materialized_views_exist(engine: Engine) -> None:
    with engine.connect() as connection:
        names = {row[0] for row in connection.execute(text("SELECT matviewname FROM pg_matviews"))}
    assert EXPECTED_VIEWS <= names


def test_overview_view_reflects_seed_after_refresh(seeded_session: Session) -> None:
    row = seeded_session.execute(text("SELECT total_trajets, nb_nuit FROM mv_overview_kpi")).one()
    assert row.total_trajets == 15
    assert row.nb_nuit == 3


CARBON_VIEWS = {"mv_co2_comparaison", "mv_carbon_density", "mv_co2_distribution"}


def test_carbon_views_exist(engine: Engine) -> None:
    with engine.connect() as connection:
        names = {row[0] for row in connection.execute(text("SELECT matviewname FROM pg_matviews"))}
    assert CARBON_VIEWS <= names


def test_co2_comparaison_view_reflects_seed(carbon_session: Session) -> None:
    rows = carbon_session.execute(
        text("SELECT nb_trajets, train_pkm, train_emissions_g FROM mv_co2_comparaison")
    ).all()
    # Vue train-only, par tranche de distance : les 15 trains du seed s'y répartissent.
    assert sum(row.nb_trajets for row in rows) == 15
    assert all(row.train_pkm > 0 and row.train_emissions_g > 0 for row in rows)


def test_co2_distribution_view_has_both_modes(carbon_session: Session) -> None:
    rows = carbon_session.execute(
        text("SELECT mode, co2_median FROM mv_co2_distribution ORDER BY mode")
    ).all()
    by_mode = {row.mode: row.co2_median for row in rows}
    assert set(by_mode) == {"flight", "train"}
    assert by_mode["train"] < by_mode["flight"]  # le train émet bien moins par pkm
