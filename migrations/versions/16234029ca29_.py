"""empty message

Revision ID: 16234029ca29
Revises: 5055ede82366
Create Date: 2024-05-21 14:42:18.559503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16234029ca29'
down_revision: Union[str, None] = '5055ede82366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
