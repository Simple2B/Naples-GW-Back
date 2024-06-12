"""empty message

Revision ID: 44448a38efea
Revises: 9ec9d7903334
Create Date: 2024-06-12 14:33:49.450556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44448a38efea'
down_revision: Union[str, None] = '9ec9d7903334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
