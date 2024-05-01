import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid


class Amenity(db.Model, ModelMixin):
    __tablename__ = "amenities"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    value: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    def __repr__(self):
        return f"<{self.uuid}:{self.value} >"
