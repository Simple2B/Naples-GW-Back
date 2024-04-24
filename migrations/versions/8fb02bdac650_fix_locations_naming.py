"""fix locations naming

Revision ID: 8fb02bdac650
Revises: 8a5aaaa02c24
Create Date: 2024-04-24 17:18:37.288459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fb02bdac650'
down_revision: Union[str, None] = '8a5aaaa02c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cities', sa.Column('county_id', sa.Integer(), nullable=False))
    op.drop_constraint('cities_region_id_fkey', 'cities', type_='foreignkey')
    op.create_foreign_key(None, 'cities', 'counties', ['county_id'], ['id'])
    op.drop_column('cities', 'region_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cities', sa.Column('region_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'cities', type_='foreignkey')
    op.create_foreign_key('cities_region_id_fkey', 'cities', 'counties', ['region_id'], ['id'])
    op.drop_column('cities', 'county_id')
    # ### end Alembic commands ###
