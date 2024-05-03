import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid


class File(db.Model, ModelMixin):
    __tablename__ = "files"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    original_name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    type: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    url: orm.Mapped[str] = orm.mapped_column(sa.String(256), unique=True)

    owner_type: orm.Mapped[str] = orm.mapped_column()

    owner_id: orm.Mapped[int] = orm.mapped_column()

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
