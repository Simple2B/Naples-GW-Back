from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from naples.schemas.contact_request import ContactRequestStatus

from .utils import create_uuid

if TYPE_CHECKING:
    from .item import Item
    from .store import Store


class ContactRequest(db.Model):
    __tablename__ = "contact_requests"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(128))
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(128))
    email: orm.Mapped[str] = orm.mapped_column(sa.String(512))
    phone: orm.Mapped[str] = orm.mapped_column(sa.String(64))
    message: orm.Mapped[str] = orm.mapped_column(sa.Text)
    check_in: orm.Mapped[datetime] = orm.mapped_column()
    check_out: orm.Mapped[datetime] = orm.mapped_column()
    status: orm.Mapped[str] = orm.mapped_column(default=ContactRequestStatus.CREATED.value)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))
    item_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("items.id"))

    store: orm.Mapped["Store"] = orm.relationship(back_populates="_contact_requests")
    item: orm.Mapped["Item"] = orm.relationship(
        back_populates="_contact_requests",
    )

    @property
    def store_uuid(self):
        return self.store.uuid

    @property
    def item_uuid(self):
        return self.item.uuid if self.item else None

    def __repr__(self):
        return f"<ContactRequest [{self.uuid}]: Name - [{self.first_name} {self.last_name}]>"
