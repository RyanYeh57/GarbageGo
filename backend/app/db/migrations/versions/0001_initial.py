"""initial schema

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def point():
    return Geometry("POINT", srid=4326, spatial_index=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "collection_stops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_index", sa.Integer, nullable=False, unique=True),
        sa.Column("area", sa.Text, nullable=False),
        sa.Column("village", sa.Text, nullable=False),
        sa.Column("caption", sa.Text, nullable=False),
        sa.Column("task_type", sa.Text, nullable=False),
        sa.Column("car_licence", sa.Text),
        sa.Column("geom", point()),
        sa.Column("geocode_source", sa.Text),
        sa.Column("geocode_level", sa.Text),
        sa.Column("source_dataset_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_collection_stops_geom", "collection_stops", ["geom"], postgresql_using="gist")

    op.create_table(
        "collection_schedules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("stop_id", sa.Integer, sa.ForeignKey("collection_stops.id"), nullable=False),
        sa.Column("day_index", sa.SmallInteger, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.UniqueConstraint("stop_id", "day_index", "kind"),
    )

    op.create_table(
        "vehicle_observations",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("car", sa.Text, nullable=False),
        sa.Column("line_id", sa.Text),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("geom", point(), nullable=False),
        sa.Column("speed", sa.Integer),
        sa.Column("over_speed", sa.Boolean),
        sa.Column("location_text", sa.Text),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("raw", JSONB, nullable=False),
        sa.UniqueConstraint("car", "observed_at"),
    )
    op.create_index("ix_vehicle_observations_observed_at", "vehicle_observations", ["observed_at"])
    op.create_index("ix_vehicle_observations_geom", "vehicle_observations", ["geom"], postgresql_using="gist")

    op.create_table(
        "stop_arrivals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("stop_id", sa.Integer, sa.ForeignKey("collection_stops.id"), nullable=False),
        sa.Column("car", sa.Text, nullable=False),
        sa.Column("service_date", sa.Date, nullable=False),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.Text, nullable=False),
        sa.UniqueConstraint("stop_id", "car", "service_date"),
    )


def downgrade() -> None:
    op.drop_table("stop_arrivals")
    op.drop_table("vehicle_observations")
    op.drop_table("collection_schedules")
    op.drop_table("collection_stops")
