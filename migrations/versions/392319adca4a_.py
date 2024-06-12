"""empty message

Revision ID: 392319adca4a
Revises: 14a571f23eda
Create Date: 2024-06-12 20:00:48.574624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '392319adca4a'
down_revision: Union[str, None] = '14a571f23eda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
