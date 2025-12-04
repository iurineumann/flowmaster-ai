"""add pat column to ado connections

Revision ID: v2_add_pat
Revises: af5ddafbf8d6
Create Date: 2025-12-04 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'v2_add_pat'
down_revision: Union[str, None] = 'af5ddafbf8d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('user_ado_connections', sa.Column('personal_access_token', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('user_ado_connections', 'personal_access_token')