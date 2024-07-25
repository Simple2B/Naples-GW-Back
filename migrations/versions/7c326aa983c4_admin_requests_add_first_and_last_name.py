"""admin requests - add first and last name

Revision ID: 7c326aa983c4
Revises: e7f3b188add9
Create Date: 2024-07-25 10:17:37.171561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c326aa983c4'
down_revision: Union[str, None] = 'e7f3b188add9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
