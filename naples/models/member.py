import email

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .store import Store


class Member(db.Model, ModelMixin):
    __tablename__ = "members"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
        index=True,
        validator=email,
    )

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    # TODO: check max length of avatar url
    avatar_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
