"""uuid_default_and_unique

Revision ID: 4d1eb631d8bd
Revises: 9a7e9e43c48e
Create Date: 2024-05-03 13:51:26.769529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d1eb631d8bd'
down_revision: Union[str, None] = '9a7e9e43c48e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('amenities', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'amenities', ['uuid'])
    op.alter_column('cities', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'cities', ['uuid'])
    op.alter_column('counties', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'counties', ['uuid'])
    op.alter_column('fees', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'fees', ['uuid'])
    op.alter_column('files', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'files', ['uuid'])
    op.alter_column('floor_plan_markers', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'floor_plan_markers', ['uuid'])
    op.alter_column('floor_plans', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'floor_plans', ['uuid'])
    op.alter_column('items', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'items', ['uuid'])
    op.alter_column('members', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'members', ['uuid'])
    op.alter_column('rates', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'rates', ['uuid'])
    op.alter_column('states', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'states', ['uuid'])
    op.alter_column('stores', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'stores', ['uuid'])
    op.alter_column('users', 'uuid',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.String(length=32),
               existing_nullable=False)
    op.create_unique_constraint(None, 'users', ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.alter_column('users', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'stores', type_='unique')
    op.alter_column('stores', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'states', type_='unique')
    op.alter_column('states', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'rates', type_='unique')
    op.alter_column('rates', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'members', type_='unique')
    op.alter_column('members', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'items', type_='unique')
    op.alter_column('items', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'floor_plans', type_='unique')
    op.alter_column('floor_plans', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'floor_plan_markers', type_='unique')
    op.alter_column('floor_plan_markers', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'files', type_='unique')
    op.alter_column('files', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'fees', type_='unique')
    op.alter_column('fees', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'counties', type_='unique')
    op.alter_column('counties', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'cities', type_='unique')
    op.alter_column('cities', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint(None, 'amenities', type_='unique')
    op.alter_column('amenities', 'uuid',
               existing_type=sa.String(length=32),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    # ### end Alembic commands ###
