"""phase3a_session_tc_schema

Revision ID: c743810ef12a
Revises: b5819fcb4ae3
Create Date: 2026-10-31 05:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c743810ef12a'
down_revision: Union[str, None] = 'b5819fcb4ae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tc_prefix and tc_counter to sessions with server_defaults for clean upgrades
    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tc_prefix', sa.String(length=12), server_default='TC', nullable=False))
        batch_op.add_column(sa.Column('tc_counter', sa.Integer(), server_default='0', nullable=False))

    # Add unique constraint on (session_id, tc_id) and index on (session_id, position)
    with op.batch_alter_table('test_cases', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_test_cases_session_id_tc_id', ['session_id', 'tc_id'])
        batch_op.create_index('ix_test_cases_session_id_position', ['session_id', 'position'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('test_cases', schema=None) as batch_op:
        batch_op.drop_index('ix_test_cases_session_id_position')
        batch_op.drop_constraint('uq_test_cases_session_id_tc_id', type_='unique')

    with op.batch_alter_table('sessions', schema=None) as batch_op:
        batch_op.drop_column('tc_counter')
        batch_op.drop_column('tc_prefix')
