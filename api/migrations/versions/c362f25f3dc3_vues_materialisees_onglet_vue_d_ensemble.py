"""vues materialisees onglet vue d ensemble

Revision ID: c362f25f3dc3
Revises: 096b998418ee
Create Date: 2026-06-25 17:51:51.058040

"""

from collections.abc import Sequence

from alembic import op

from etl.views import create_views, drop_views

# revision identifiers, used by Alembic.
revision: str = "c362f25f3dc3"
down_revision: str | Sequence[str] | None = "096b998418ee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée les vues matérialisées de l'onglet Vue d'ensemble + leurs index uniques."""
    create_views(op.get_bind())


def downgrade() -> None:
    """Supprime les vues matérialisées."""
    drop_views(op.get_bind())
