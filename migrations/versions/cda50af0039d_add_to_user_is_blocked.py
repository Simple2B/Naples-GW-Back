"""add to user is blocked

Revision ID: cda50af0039d
Revises: b2a84b4e7e1a
Create Date: 2024-06-26 15:52:11.535984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cda50af0039d'
down_revision: Union[str, None] = 'b2a84b4e7e1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_blocked', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_blocked')
    # ### end Alembic commands ###
