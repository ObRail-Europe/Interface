"""Tests du modèle ORM `Trajet` (table trajets)."""

from datetime import date

from sqlalchemy.orm import Session

from models import Trajet

EXPECTED_COLUMNS = {
    "id", "source", "trip_id", "mode", "destination", "trip_short_name",
    "agency_name", "agency_timezone", "service_id", "route_id", "route_type",
    "route_short_name", "route_long_name", "departure_station", "departure_city",
    "departure_country", "departure_time", "departure_parent_station",
    "arrival_station", "arrival_city", "arrival_country", "arrival_time",
    "arrival_parent_station", "service_start_date", "service_end_date",
    "days_of_week", "is_night_train", "distance_km", "co2_per_pkm", "emissions_co2",
    "departure_citycode", "arrival_citycode",
}  # fmt: skip


def test_tablename() -> None:
    assert Trajet.__tablename__ == "trajets"


def test_primary_key_is_surrogate() -> None:
    pk = [c.name for c in Trajet.__table__.primary_key.columns]
    assert pk == ["id"]


def test_columns_match_source() -> None:
    assert set(Trajet.__table__.columns.keys()) == EXPECTED_COLUMNS


def test_indexes_declared() -> None:
    indexed = {c.name for c in Trajet.__table__.columns if c.index}
    expected = {
        "trip_id",
        "mode",
        "agency_name",
        "departure_city",
        "departure_country",
        "arrival_city",
        "arrival_country",
        "is_night_train",
        "service_start_date",
        "service_end_date",
        "departure_citycode",
        "arrival_citycode",
    }
    assert expected <= indexed


def test_insert_roundtrip(session: Session) -> None:
    trajet = Trajet(
        source="BOTN",
        trip_id="ÖBB NJ 40469",
        mode="train",
        agency_name="ÖBB-Personenverkehr AG",
        departure_city="Strasbourg",
        departure_country="FR",
        departure_time="00:01:00",
        arrival_city="Berlin",
        arrival_country="DE",
        arrival_time="08:19:00",
        service_start_date=date(2024, 12, 15),
        service_end_date=date(2025, 12, 13),
        days_of_week="1000001",
        is_night_train=True,
        distance_km=789.71,
        co2_per_pkm=3.73,
        emissions_co2=2945.618,
    )
    session.add(trajet)
    session.flush()  # exécute l'INSERT sans valider (rollback en teardown)

    assert trajet.id is not None  # PK surrogate auto-générée
    got = session.get(Trajet, trajet.id)
    assert got is not None
    assert got.departure_city == "Strasbourg"
    assert got.is_night_train is True
    assert got.distance_km == 789.71
