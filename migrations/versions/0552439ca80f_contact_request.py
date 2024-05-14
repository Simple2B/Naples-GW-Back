"""contact_request

Revision ID: 0552439ca80f
Revises: 347875a3a2da
Create Date: 2024-05-14 10:14:10.674222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0552439ca80f'
down_revision: Union[str, None] = '347875a3a2da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contact_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=32), nullable=False),
    sa.Column('first_name', sa.String(length=128), nullable=False),
    sa.Column('last_name', sa.String(length=128), nullable=False),
    sa.Column('email', sa.String(length=512), nullable=False),
    sa.Column('phone', sa.String(length=64), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('check_in', sa.DateTime(), nullable=False),
    sa.Column('check_out', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=64), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('contact_requests')
    # ### end Alembic commands ###
