import sqlalchemy as sa

from datetime import datetime
from sqlalchemy import orm
from typing import TYPE_CHECKING


from naples.database import db
from naples import schemas as s
from .utils import ModelMixin, create_uuid


if TYPE_CHECKING:
    from .store import Store
    from .item import Item
    from .file import File


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

    title: orm.Mapped[str] = orm.mapped_column(default=s.MemberType.REALTOR.value)

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    avatar_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))

    avatar: orm.Mapped["File"] = orm.relationship()

    _items: orm.Mapped[list["Item"]] = orm.relationship("Item", viewonly=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    @property
    def items(self):
        return [item for item in self._items if not item.is_deleted]

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar and not self.avatar.is_deleted else ""

    def mark_as_deleted(self):
        self.is_deleted = True
        self.email = f"{self.email}-deleted-{datetime.now().timestamp()}"

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
