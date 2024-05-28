"""merge

Revision ID: c103e76a9a12
Revises: 1fc325a4be63, 9e7ef0a78034
Create Date: 2024-05-28 13:36:51.567889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c103e76a9a12'
down_revision: Union[str, None] = ('1fc325a4be63', '9e7ef0a78034') # type: ignore
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
