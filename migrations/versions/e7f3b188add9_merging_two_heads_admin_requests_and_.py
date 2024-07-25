"""merging two heads - admin requests and protect

Revision ID: e7f3b188add9
Revises: 02462e974330, 2a9bc42db753
Create Date: 2024-07-25 10:13:01.783169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f3b188add9'
down_revision: Union[str, None] = ('02462e974330', '2a9bc42db753') # type: ignore
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
