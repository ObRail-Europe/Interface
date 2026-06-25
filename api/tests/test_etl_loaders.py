"""Tests des loaders ETL (cast typé + COPY) sur de petits CSV temporaires."""

from datetime import date
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from etl.loaders import load_clusters, load_trajets, load_villes
from models import Cluster, Trajet, Ville


def test_load_villes_casts_types(session: Session, tmp_path: Path) -> None:
    csv_file = tmp_path / "villes.csv"
    csv_file.write_text(
        "citycode,city_name,has_gare,population_insee,accessibilite_ord\n"
        "01004,Ambérieu,True,15934.0,3\n"
        "01005,Ambérieux,False,1906.0,\n",
        encoding="utf-8",
    )
    assert load_villes(session, csv_file) == 2
    session.flush()

    v = session.get(Ville, "01004")
    assert v is not None
    assert v.has_gare is True
    assert v.population_insee == 15934.0
    assert v.accessibilite_ord == 3
    assert session.get(Ville, "01005").accessibilite_ord is None  # champ vide → None


def test_load_clusters_casts_float_bool(session: Session, tmp_path: Path) -> None:
    csv_file = tmp_path / "clusters.csv"
    csv_file.write_text(
        "row_id,city_name,cluster,niveau_fragilite,has_gare,accessibilite_ord\n"
        "8591,Abbeville,0,Faible,1.0,3.0\n",
        encoding="utf-8",
    )
    assert load_clusters(session, csv_file) == 1
    session.flush()

    c = session.get(Cluster, 8591)
    assert c is not None
    assert c.has_gare is True  # "1.0" → True
    assert c.accessibilite_ord == 3  # "3.0" → 3


def test_load_trajets_via_copy(engine: Engine, tmp_path: Path) -> None:
    csv_file = tmp_path / "trajets.csv"
    csv_file.write_text(
        "trip_id,mode,departure_city,arrival_city,is_night_train,distance_km,service_start_date\n"
        "T1,train,Strasbourg,Berlin,True,789.71,20241215\n",
        encoding="utf-8",
    )
    # COPY écrit hors de la transaction de test → on isole avec un TRUNCATE avant/après.
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE trajets RESTART IDENTITY"))
    try:
        load_trajets(engine, csv_file)
        with Session(engine) as s:
            t = s.execute(select(Trajet)).scalars().first()
            assert t is not None
            assert t.departure_city == "Strasbourg"
            assert t.is_night_train is True
            assert t.distance_km == 789.71
            assert t.service_start_date == date(2024, 12, 15)
    finally:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE trajets RESTART IDENTITY"))
