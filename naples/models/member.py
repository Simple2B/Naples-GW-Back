import sqlalchemy as sa

from datetime import datetime
from sqlalchemy import orm
from typing import TYPE_CHECKING

from naples.database import db
from .utils import ModelMixin, create_uuid


if TYPE_CHECKING:
    from .store import Store
    from .item import Item


class Member(db.Model, ModelMixin):
    __tablename__ = "members"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128), default=False)

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(16), default="")

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    avatar_url: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="")  # //TODO: reafactor to @property

    _items: orm.Mapped[list["Item"]] = orm.relationship("Item", viewonly=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    @property
    def items(self):
        return [item for item in self._items if not item.is_deleted]

    def mark_as_deleted(self):
        self.is_deleted = True
        self.email = f"{self.email}-deleted-{datetime.now().timestamp()}"

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
