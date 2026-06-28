"""vue mv_distance_hist (histogramme distances)

Revision ID: ed8e5a8a2b63
Revises: 047255c8d3a9
Create Date: 2026-06-27 10:43:04.784397

"""

from collections.abc import Sequence

from alembic import op

from obrail_database.etl.views import create_views, drop_views

# revision identifiers, used by Alembic.
revision: str = "ed8e5a8a2b63"
down_revision: str | Sequence[str] | None = "047255c8d3a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VIEWS = ("mv_distance_hist",)


def upgrade() -> None:
    """Crée la vue matérialisée mv_distance_hist + son index unique."""
    create_views(op.get_bind(), _VIEWS)


def downgrade() -> None:
    """Supprime la vue matérialisée mv_distance_hist."""
    drop_views(op.get_bind(), _VIEWS)
