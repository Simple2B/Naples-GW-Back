"""fix locations relationship

Revision ID: fbcc13a1dc0f
Revises: 8fb02bdac650
Create Date: 2024-04-24 17:46:19.211571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbcc13a1dc0f'
down_revision: Union[str, None] = '8fb02bdac650'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
