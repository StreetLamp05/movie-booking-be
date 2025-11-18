"""merge final heads

Revision ID: ffffffffffffffff
Revises: dbdbcfbf5c02, ff939d6418da
Create Date: 2025-11-17 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ffffffffffffffff'
down_revision = ('dbdbcfbf5c02', 'ff939d6418da')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only revision. No schema changes.
    pass


def downgrade() -> None:
    # No-op downgrade for merge-only revision.
    pass
