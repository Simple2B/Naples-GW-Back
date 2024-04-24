from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import ModelMixin

if TYPE_CHECKING:
    from .city import City
    from .state import State


class County(db.Model, ModelMixin):
    __tablename__ = "counties"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    state_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("states.id"))

    state: orm.Mapped["State"] = orm.relationship("State", back_populates="counties")

    cities: orm.Mapped[list["City"]] = orm.relationship("City", back_populates="county")

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
