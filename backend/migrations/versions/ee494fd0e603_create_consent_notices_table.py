
"""create consent notices table

Revision ID: ee494fd0e603
Revises: 8e09779e611c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ee494fd0e603'
down_revision: Union[str, Sequence[str], None] = '8e09779e611c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'consent_notices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purpose_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['purpose_id'],
            ['consent_purposes.id']
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'purpose_id',
            'version',
            name='uq_consent_notice_purpose_version'
        )
    )

    op.create_index(
        op.f('ix_consent_notices_purpose_id'),
        'consent_notices',
        ['purpose_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_consent_notices_purpose_id'),
        table_name='consent_notices'
    )
    op.drop_table('consent_notices')
