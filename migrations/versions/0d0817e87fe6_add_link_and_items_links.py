"""add link and items links

Revision ID: 0d0817e87fe6
Revises: be0943e6041d
Create Date: 2024-06-07 21:17:38.864934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d0817e87fe6'
down_revision: Union[str, None] = 'be0943e6041d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=32), nullable=False),
    sa.Column('type', sa.String(length=64), nullable=False),
    sa.Column('url', sa.String(length=256), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('items_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('link_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.ForeignKeyConstraint(['link_id'], ['links.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('items_links')
    op.drop_table('links')
    # ### end Alembic commands ###
