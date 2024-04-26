"""fix item - rieltor

Revision ID: 5d73af94c181
Revises: cb3a2d0dbd8b
Create Date: 2024-04-26 16:21:26.201635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d73af94c181'
down_revision: Union[str, None] = 'cb3a2d0dbd8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('files_owner_id_fkey', 'files', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('files_owner_id_fkey', 'files', 'users', ['owner_id'], ['id'])
    # ### end Alembic commands ###
