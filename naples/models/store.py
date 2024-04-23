import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid, datetime_utc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class Store(db.Model, ModelMixin):
    __tablename__ = "stores"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    header: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    sub_header: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    logo_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    about_us: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    user: orm.Mapped["User"] = orm.relationship(back_populates="store")

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    def __repr__(self):
        return f"<{self.id}:{self.name} >"
