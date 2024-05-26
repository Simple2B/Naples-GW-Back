"""add to bookedate from and to dates

Revision ID: ff38078f9b44
Revises: 4d2e85e8c80f
Create Date: 2024-05-26 09:24:30.405494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ff38078f9b44'
down_revision: Union[str, None] = '4d2e85e8c80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('booked_dates', sa.Column('from_date', sa.DateTime(), nullable=False))
    op.add_column('booked_dates', sa.Column('to_date', sa.DateTime(), nullable=False))
    op.drop_column('booked_dates', 'date')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('booked_dates', sa.Column('date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.drop_column('booked_dates', 'to_date')
    op.drop_column('booked_dates', 'from_date')
    # ### end Alembic commands ###
