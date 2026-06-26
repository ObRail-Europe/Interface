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
