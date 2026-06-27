"""vue mv_liaisons (carte des liaisons)

Revision ID: 047255c8d3a9
Revises: c362f25f3dc3
Create Date: 2026-06-26 10:57:20.012684

"""

from collections.abc import Sequence

from alembic import op

from etl.views import create_views, drop_views

# revision identifiers, used by Alembic.
revision: str = "047255c8d3a9"
down_revision: str | Sequence[str] | None = "c362f25f3dc3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VIEWS = ("mv_liaisons",)


def upgrade() -> None:
    """Crée la vue matérialisée mv_liaisons + son index unique."""
    create_views(op.get_bind(), _VIEWS)


def downgrade() -> None:
    """Supprime la vue matérialisée mv_liaisons."""
    drop_views(op.get_bind(), _VIEWS)
