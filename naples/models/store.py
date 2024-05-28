from datetime import datetime
import sqlalchemy as sa
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
    from .contact_request import ContactRequest


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

    url: orm.Mapped[str] = orm.mapped_column(
        sa.String(256), unique=True, default=""
    )  # TODO: Re implement this to generate a unique url on store creation, may be using UUID, so that users can change the url later

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
    _contact_requests: orm.Mapped[list["ContactRequest"]] = orm.relationship(back_populates="store", viewonly=True)

    main_media_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    logo_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    about_us_description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="", server_default="")

    about_us_main_media_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"), nullable=True)

    _main_media: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[main_media_id])

    _about_us_main_media: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[about_us_main_media_id])

    _logo: orm.Mapped["File"] = orm.relationship(viewonly=True, foreign_keys=[logo_id])

    @property
    def main_media(self):
        return self._main_media if self._main_media and not self._main_media.is_deleted else None

    @property
    def about_us_main_media(self):
        return (
            self._about_us_main_media
            if self._about_us_main_media and not self._about_us_main_media.is_deleted
            else None
        )

    @property
    def main_media_url(self):
        return self.main_media.url if self.main_media else ""

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
    def logo_url(self):
        return self.logo.url if self.logo else ""

    @property
    def about_us(self) -> s.StoreAboutUs:
        return s.StoreAboutUs(
            about_us_description=self.about_us_description,
            about_us_main_media=self.about_us_main_media,
        )

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
    def contact_requests(self):
        return [contact_request for contact_request in self._contact_requests if not contact_request.is_deleted]

    def get_item_by_uuid(self, item_uuid: str):
        for item in self.items:
            if item.uuid == item_uuid and not item.is_deleted:
                return item
        else:
            return None

    def __repr__(self):
        return f"<{self.id}:{self.url} >"
