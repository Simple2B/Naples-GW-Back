"""empty message

Revision ID: 4d2e85e8c80f
Revises: 9ebadbaa5301
Create Date: 2024-05-26 09:23:34.232903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d2e85e8c80f'
down_revision: Union[str, None] = '9ebadbaa5301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
