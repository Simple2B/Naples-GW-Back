"""to file add updated at

Revision ID: 78511b1d8cd0
Revises: 8786fc892da7
Create Date: 2024-06-19 14:58:28.640367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78511b1d8cd0'
down_revision: Union[str, None] = '8786fc892da7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('files', 'updated_at')
    # ### end Alembic commands ###
