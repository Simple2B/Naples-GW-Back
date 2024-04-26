import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .store import Store
    from .item import Item


class Member(db.Model, ModelMixin):
    __tablename__ = "members"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128), default=False)

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    avatar_url: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="")

    items: orm.Mapped[list["Item"]] = orm.relationship("Item", viewonly=True)

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
