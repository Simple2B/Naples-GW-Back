"""empty message

Revision ID: 6f5a5088a526
Revises: 512a8a6bfe24
Create Date: 2024-07-25 15:12:39.191892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f5a5088a526'
down_revision: Union[str, None] = '512a8a6bfe24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
