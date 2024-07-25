"""empty message

Revision ID: 5cfa19d45681
Revises: e7b573b047a9
Create Date: 2024-07-25 14:22:59.026822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cfa19d45681'
down_revision: Union[str, None] = 'e7b573b047a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
