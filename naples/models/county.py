from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import ModelMixin, create_uuid

if TYPE_CHECKING:
    from .city import City
    from .state import State


class County(db.Model, ModelMixin):
    __tablename__ = "counties"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    state_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("states.id"))

    state: orm.Mapped["State"] = orm.relationship()

    cities: orm.Mapped[list["City"]] = orm.relationship("City", viewonly=True)

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
