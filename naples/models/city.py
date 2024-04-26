from typing import TYPE_CHECKING
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin

if TYPE_CHECKING:
    from .county import County


class City(db.Model, ModelMixin):
    __tablename__ = "cities"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    county_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("counties.id"))

    county: orm.Mapped["County"] = orm.relationship()

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
