"""Database tables. The migration in migrations/versions/ is the source of truth
for the schema; these models mirror it for ORM use."""
from datetime import date, datetime, time

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, SmallInteger, Text, Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Spatial indexes are declared explicitly (GiST), not by GeoAlchemy2.
POINT = Geometry("POINT", srid=4326, spatial_index=False)


class Base(DeclarativeBase):
    pass


class CollectionStop(Base):
    __tablename__ = "collection_stops"
    __table_args__ = (Index("ix_collection_stops_geom", "geom", postgresql_using="gist"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_index: Mapped[int] = mapped_column(Integer, unique=True)  # row position in the locked 84004 file
    area: Mapped[str] = mapped_column(Text)
    village: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(Text)
    car_licence: Mapped[str | None] = mapped_column(Text)
    geom = mapped_column(POINT, nullable=True)
    geocode_source: Mapped[str | None] = mapped_column(Text)  # local / tgos / manual
    geocode_level: Mapped[str | None] = mapped_column(Text)  # exact / approx_* / suspect
    source_dataset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CollectionSchedule(Base):
    __tablename__ = "collection_schedules"
    __table_args__ = (UniqueConstraint("stop_id", "day_index", "kind"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("collection_stops.id"))
    day_index: Mapped[int] = mapped_column(SmallInteger)  # 84004 d1..d7, NOT a weekday
    kind: Mapped[str] = mapped_column(Text)  # general / recycle
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)


class VehicleObservation(Base):
    __tablename__ = "vehicle_observations"
    __table_args__ = (
        UniqueConstraint("car", "observed_at"),
        Index("ix_vehicle_observations_observed_at", "observed_at"),
        Index("ix_vehicle_observations_geom", "geom", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    car: Mapped[str] = mapped_column(Text)
    line_id: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    geom = mapped_column(POINT, nullable=False)
    speed: Mapped[int | None] = mapped_column(Integer)
    over_speed: Mapped[bool | None] = mapped_column(Boolean)
    location_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)  # api / historical
    raw: Mapped[dict] = mapped_column(JSONB)


class StopArrival(Base):
    __tablename__ = "stop_arrivals"
    __table_args__ = (UniqueConstraint("stop_id", "car", "service_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("collection_stops.id"))
    car: Mapped[str] = mapped_column(Text)
    service_date: Mapped[date] = mapped_column(Date)
    arrived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    method: Mapped[str] = mapped_column(Text)
