"""add billing_info table

Revision ID: 480f1a9532ed
Revises: ff939d6418da
Create Date: 2025-10-28 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '480f1a9532ed'
down_revision = 'ff939d6418da'
branch_labels = None
depends_on = None


def upgrade():
    # Use existing card_type enum
    card_type_enum = postgresql.ENUM('credit', 'debit', name='card_type', create_type=False)
    
    # Create billing_info table
    op.create_table('billing_info',
        sa.Column('billing_info_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('card_type', card_type_enum, nullable=False),
        sa.Column('card_number', sa.String(length=16), nullable=False),
        sa.Column('card_exp', sa.String(length=5), nullable=False),
        sa.Column('billing_street', sa.String(length=255), nullable=False),
        sa.Column('billing_state', sa.String(length=2), nullable=False),
        sa.Column('billing_zip_code', sa.String(length=5), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('billing_info_id')
    )


def downgrade():
    op.drop_table('billing_info')
    # Drop the enum type
    postgresql.ENUM(name='card_type').drop(op.get_bind(), checkfirst=True)
