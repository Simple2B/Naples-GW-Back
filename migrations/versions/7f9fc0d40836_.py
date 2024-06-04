"""empty message

Revision ID: 7f9fc0d40836
Revises: da645a1270f2
Create Date: 2024-06-04 09:32:27.020645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9fc0d40836'
down_revision: Union[str, None] = 'da645a1270f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
