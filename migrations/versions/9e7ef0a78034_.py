"""empty message

Revision ID: 9e7ef0a78034
Revises: d19b7c9e489d
Create Date: 2024-05-28 11:02:38.439355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e7ef0a78034'
down_revision: Union[str, None] = 'd19b7c9e489d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
