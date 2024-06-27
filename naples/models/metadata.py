import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid


class Metadata(db.Model, ModelMixin):
    __tablename__ = "metadatas"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    key: orm.Mapped[str] = orm.mapped_column(sa.String(128), unique=True, nullable=False)

    value: orm.Mapped[str] = orm.mapped_column(sa.String(256))

    def __repr__(self):
        return f"<{self.id}:{self.key} >"
