"""store_title_subtitle

Revision ID: 50658e049907
Revises: cd80500d43be
Create Date: 2024-05-13 10:25:11.225644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50658e049907'
down_revision: Union[str, None] = 'cd80500d43be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stores', sa.Column('title_value', sa.String(length=256), server_default='', nullable=False))
    op.add_column('stores', sa.Column('title_color', sa.String(length=16), server_default='#000000', nullable=False))
    op.add_column('stores', sa.Column('title_font_size', sa.Integer(), server_default='24', nullable=False))
    op.add_column('stores', sa.Column('sub_title_value', sa.String(length=256), server_default='', nullable=False))
    op.add_column('stores', sa.Column('sub_title_color', sa.String(length=16), server_default='#000000', nullable=False))
    op.add_column('stores', sa.Column('sub_title_font_size', sa.Integer(), server_default='16', nullable=False))
    op.drop_column('stores', 'header')
    op.drop_column('stores', 'sub_header')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stores', sa.Column('sub_header', sa.VARCHAR(length=256), autoincrement=False, nullable=False))
    op.add_column('stores', sa.Column('header', sa.VARCHAR(length=256), autoincrement=False, nullable=False))
    op.drop_column('stores', 'sub_title_font_size')
    op.drop_column('stores', 'sub_title_color')
    op.drop_column('stores', 'sub_title_value')
    op.drop_column('stores', 'title_font_size')
    op.drop_column('stores', 'title_color')
    op.drop_column('stores', 'title_value')
    # ### end Alembic commands ###
