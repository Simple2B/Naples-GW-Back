import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid


class Location(db.Model, ModelMixin):
    __tablename__ = "locations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)
    longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
