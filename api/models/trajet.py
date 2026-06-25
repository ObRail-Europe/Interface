"""Modèle ORM de la table `trajets` (source : routes_france.csv)."""

from datetime import date

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Trajet(Base):
    """Trajet ferroviaire (desserte) : horaires, géographie, calendrier et émissions de CO₂."""

    __tablename__ = "trajets"

    # Clé technique (surrogate) : trip_id n'est pas garanti unique sur ~13M lignes.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str | None] = mapped_column(String)
    trip_id: Mapped[str | None] = mapped_column(String, index=True)
    mode: Mapped[str | None] = mapped_column(String, index=True)
    destination: Mapped[str | None] = mapped_column(String)
    trip_short_name: Mapped[str | None] = mapped_column(String)
    agency_name: Mapped[str | None] = mapped_column(String, index=True)
    agency_timezone: Mapped[str | None] = mapped_column(String)
    service_id: Mapped[str | None] = mapped_column(String)
    route_id: Mapped[str | None] = mapped_column(String)
    route_type: Mapped[int | None]
    route_short_name: Mapped[str | None] = mapped_column(String)
    route_long_name: Mapped[str | None] = mapped_column(String)
    departure_station: Mapped[str | None] = mapped_column(String)
    departure_city: Mapped[str | None] = mapped_column(String, index=True)
    departure_country: Mapped[str | None] = mapped_column(String(2), index=True)
    # Heures au format GTFS (peuvent dépasser 24h) → stockées en texte.
    departure_time: Mapped[str | None] = mapped_column(String)
    departure_parent_station: Mapped[str | None] = mapped_column(String)
    arrival_station: Mapped[str | None] = mapped_column(String)
    arrival_city: Mapped[str | None] = mapped_column(String, index=True)
    arrival_country: Mapped[str | None] = mapped_column(String(2), index=True)
    arrival_time: Mapped[str | None] = mapped_column(String)
    arrival_parent_station: Mapped[str | None] = mapped_column(String)
    service_start_date: Mapped[date | None] = mapped_column(index=True)
    service_end_date: Mapped[date | None] = mapped_column(index=True)
    days_of_week: Mapped[str | None] = mapped_column(String(7))  # bitmask Lun..Dim
    is_night_train: Mapped[bool | None] = mapped_column(index=True)
    distance_km: Mapped[float | None]
    co2_per_pkm: Mapped[float | None]
    emissions_co2: Mapped[float | None]
    # Rattachement (souple, sans FK) à `villes`, résolu par nom lors de l'ETL.
    departure_citycode: Mapped[str | None] = mapped_column(String(10), index=True)
    arrival_citycode: Mapped[str | None] = mapped_column(String(10), index=True)

    def __repr__(self) -> str:
        return f"<Trajet id={self.id} {self.departure_city!r}->{self.arrival_city!r}>"
