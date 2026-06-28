"""vues qualité (complétude, anomalies, volumétrie)

Revision ID: e3ec1a27ba57
Revises: 9b7563d956dd
Create Date: 2026-06-28 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

from etl.views import create_views, drop_views

# revision identifiers, used by Alembic.
revision: str = "e3ec1a27ba57"
down_revision: str | Sequence[str] | None = "9b7563d956dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VIEWS = ("mv_qualite_completude", "mv_qualite_anomalies", "mv_qualite_volumetrie")


def upgrade() -> None:
    """Crée les vues matérialisées de l'onglet qualité + leurs index uniques."""
    create_views(op.get_bind(), _VIEWS)


def downgrade() -> None:
    """Supprime les vues matérialisées de l'onglet qualité."""
    drop_views(op.get_bind(), _VIEWS)
