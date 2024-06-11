"""empty message

Revision ID: a239c6711b4d
Revises: 66316ab3a077
Create Date: 2024-06-11 18:07:02.738771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a239c6711b4d'
down_revision: Union[str, None] = '66316ab3a077'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
