from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import ModelMixin, create_uuid

if TYPE_CHECKING:
    from .county import County


class State(db.Model, ModelMixin):
    __tablename__ = "states"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    # in csv file this field name is "state_id"
    abbreviated_name: orm.Mapped[str] = orm.mapped_column(sa.String(2))

    counties: orm.Mapped[list["County"]] = orm.relationship("County", viewonly=True)

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
