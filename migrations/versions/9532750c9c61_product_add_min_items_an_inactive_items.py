"""product add min items an inactive_items

Revision ID: 9532750c9c61
Revises: e213f6dc8836
Create Date: 2024-06-30 19:11:22.193605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9532750c9c61'
down_revision: Union[str, None] = 'e213f6dc8836'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('inactive_items', sa.Integer(), nullable=False))
    op.drop_column('products', 'unactive_items')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('unactive_items', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('products', 'inactive_items')
    # ### end Alembic commands ###
