"""empty message

Revision ID: 7f9fc0d40836
Revises: 4c9f6b97606a
Create Date: 2024-06-04 01:27:15.486989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9fc0d40836'
down_revision: Union[str, None] = '4c9f6b97606a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
