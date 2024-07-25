"""to user add instagram, messenger, linkedin urls

Revision ID: 5cfa19d45681
Revises: 7c326aa983c4
Create Date: 2024-07-25 10:34:04.212813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cfa19d45681'
down_revision: Union[str, None] = '7c326aa983c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
