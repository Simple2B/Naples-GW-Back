"""empty message

Revision ID: da645a1270f2
Revises: 2f264434d9f6
Create Date: 2024-06-03 10:10:13.221159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da645a1270f2'
down_revision: Union[str, None] = '2f264434d9f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
