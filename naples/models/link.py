from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from naples.config import config
from .utils import ModelMixin, create_uuid, datetime_utc

CFG = config()


class Link(db.Model, ModelMixin):
    __tablename__ = "links"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    type: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    url: orm.Mapped[str] = orm.mapped_column(sa.String(256), unique=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    deleted_at: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
