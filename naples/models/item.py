from datetime import datetime


import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid, datetime_utc
from naples import schemas as s
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .store import Store


class Item(db.Model, ModelMixin):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")

    latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    deleted_at: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    address: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    stage: orm.Mapped[str] = orm.mapped_column(default=s.ItemRole.DRAFT.value)

    rieltor_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("members.id"))

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
