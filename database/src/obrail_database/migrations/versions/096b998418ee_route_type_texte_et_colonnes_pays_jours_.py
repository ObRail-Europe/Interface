"""route_type texte et colonnes pays/jours en texte (donnees avion)

Revision ID: 096b998418ee
Revises: f71902521a81
Create Date: 2026-06-25 15:54:40.105534

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "096b998418ee"
down_revision: str | Sequence[str] | None = "f71902521a81"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Élargit en texte les colonnes hétérogènes entre train et avion."""
    op.alter_column(
        "trajets",
        "route_type",
        existing_type=sa.INTEGER(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="route_type::varchar",
    )
    op.alter_column(
        "trajets",
        "departure_country",
        existing_type=sa.VARCHAR(length=2),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "trajets",
        "arrival_country",
        existing_type=sa.VARCHAR(length=2),
        type_=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "trajets",
        "days_of_week",
        existing_type=sa.VARCHAR(length=7),
        type_=sa.String(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "trajets",
        "days_of_week",
        existing_type=sa.String(),
        type_=sa.VARCHAR(length=7),
        existing_nullable=True,
    )
    op.alter_column(
        "trajets",
        "arrival_country",
        existing_type=sa.String(),
        type_=sa.VARCHAR(length=2),
        existing_nullable=True,
    )
    op.alter_column(
        "trajets",
        "departure_country",
        existing_type=sa.String(),
        type_=sa.VARCHAR(length=2),
        existing_nullable=True,
    )
    op.alter_column(
        "trajets",
        "route_type",
        existing_type=sa.String(),
        type_=sa.INTEGER(),
        existing_nullable=True,
        postgresql_using="route_type::integer",
    )
