import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import orm

from naples.database import db
from naples import schemas as s
from .utils import ModelMixin, create_uuid, datetime_utc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .item import Item
    from .member import Member
    from .file import File


class Store(db.Model, ModelMixin):
    __tablename__ = "stores"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    title_value: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="", server_default="")

    title_color: orm.Mapped[str] = orm.mapped_column(sa.String(16), default="#000000", server_default="#000000")

    title_font_size: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=24, server_default="24")

    sub_title_value: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="", server_default="")

    sub_title_color: orm.Mapped[str] = orm.mapped_column(sa.String(16), default="#000000", server_default="#000000")

    sub_title_font_size: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=16, server_default="16")

    url: orm.Mapped[str] = orm.mapped_column(sa.String(256), unique=True, default="")

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )
    phone: orm.Mapped[str] = orm.mapped_column(sa.String(16), default="")

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    user: orm.Mapped["User"] = orm.relationship(back_populates="store")

    _items: orm.Mapped[list["Item"]] = orm.relationship(viewonly=True)

    _members: orm.Mapped[list["Member"]] = orm.relationship(back_populates="store", viewonly=True)

    image_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    video_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    logo_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    _image: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[image_id])

    _video: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[video_id])

    _logo: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[logo_id])

    @property
    def image(self):
        return self._image if self._image and not self._image.is_deleted else None

    @property
    def video(self):
        return self._video if self._video and not self._video.is_deleted else None

    @property
    def logo(self):
        return self._logo if self._logo and not self._logo.is_deleted else None

    @property
    def members(self):
        return [member for member in self._members if not member.is_deleted]

    @property
    def items(self):
        return [item for item in self._items if not item.is_deleted]

    @property
    def image_url(self):
        return self.image.url if self.image else ""

    @property
    def video_url(self):
        return self.video.url if self.video else ""

    @property
    def logo_url(self):
        return self.logo.url if self.logo else ""

    @property
    def title(self) -> s.EditableText:
        return s.EditableText(
            value=self.title_value,
            color=self.title_color,
            font_size=self.title_font_size,
        )

    @property
    def sub_title(self) -> s.EditableText:
        return s.EditableText(
            value=self.sub_title_value,
            color=self.sub_title_color,
            font_size=self.sub_title_font_size,
        )

    @property
    def main_media(self):
        if self.image:
            return self.image
        elif self.video:
            return self.video
        else:
            return None

    def get_item_by_uuid(self, item_uuid: str):
        for item in self.items:
            if item.uuid == item_uuid and not item.is_deleted:
                return item
        else:
            return None

    def __repr__(self):
        return f"<{self.id}:{self.url} >"
