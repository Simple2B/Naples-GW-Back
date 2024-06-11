"""add product is deleted

Revision ID: 6ad7d35ad259
Revises: 2ff3cfe1008c
Create Date: 2024-06-11 16:33:15.650687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ad7d35ad259'
down_revision: Union[str, None] = '2ff3cfe1008c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('is_deleted', sa.Boolean(), nullable=False))
    op.drop_column('products', 'is_delete')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('is_delete', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.drop_column('products', 'is_deleted')
    # ### end Alembic commands ###
