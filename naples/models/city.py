from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid

if TYPE_CHECKING:
    from .county import County


class City(db.Model, ModelMixin):
    __tablename__ = "cities"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)
    longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    county_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("counties.id"))

    county: orm.Mapped["County"] = orm.relationship()

    @property
    def county_uuid(self) -> str:
        return self.county.uuid

    @property
    def state_uuid(self) -> str:
        return self.county.state.uuid

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
