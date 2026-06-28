"""vues carbone (comparaison avion, densité, distribution)

Revision ID: 9b7563d956dd
Revises: ed8e5a8a2b63
Create Date: 2026-06-27 11:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

from obrail_database.etl.views import create_views, drop_views

# revision identifiers, used by Alembic.
revision: str = "9b7563d956dd"
down_revision: str | Sequence[str] | None = "ed8e5a8a2b63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VIEWS = ("mv_co2_comparaison", "mv_carbon_density", "mv_co2_distribution")


def upgrade() -> None:
    """Crée les vues matérialisées de l'onglet carbone + leurs index uniques."""
    create_views(op.get_bind(), _VIEWS)


def downgrade() -> None:
    """Supprime les vues matérialisées de l'onglet carbone."""
    drop_views(op.get_bind(), _VIEWS)
