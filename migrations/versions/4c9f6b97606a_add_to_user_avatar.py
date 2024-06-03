"""add to user avatar

Revision ID: 4c9f6b97606a
Revises: da645a1270f2
Create Date: 2024-06-03 10:10:33.411365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4c9f6b97606a'
down_revision: Union[str, None] = 'da645a1270f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('billings')
    op.add_column('users', sa.Column('avatar_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'files', ['avatar_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('', 'users', type_='foreignkey')
    op.drop_column('users', 'avatar_id')
    op.create_table('billings',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('uuid', sa.VARCHAR(length=32), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('amount', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('customer_stripe_id', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('subscription_id', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('subscription_start_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('subscription_end_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('subscription_status', sa.VARCHAR(length=32), autoincrement=False, nullable=True),
    sa.Column('subscription_item_id', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='billings_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='billings_pkey'),
    sa.UniqueConstraint('uuid', name='billings_uuid_key')
    )
    # ### end Alembic commands ###
