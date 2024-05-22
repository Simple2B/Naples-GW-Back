"""add lat and long to city

Revision ID: 9ebadbaa5301
Revises: 1c8fbdc9b3b7
Create Date: 2024-05-22 11:59:03.614221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ebadbaa5301'
down_revision: Union[str, None] = '1c8fbdc9b3b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cities', sa.Column('latitude', sa.Float(), nullable=False))
    op.add_column('cities', sa.Column('longitude', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cities', 'longitude')
    op.drop_column('cities', 'latitude')
    # ### end Alembic commands ###
