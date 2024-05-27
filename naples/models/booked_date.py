import sqlalchemy as sa

from typing import TYPE_CHECKING
from sqlalchemy import orm
from datetime import datetime

from naples.database import db
from .utils import create_uuid

if TYPE_CHECKING:
    from .item import Item


class BookedDate(db.Model):
    __tablename__ = "booked_dates"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    from_date: orm.Mapped[datetime] = orm.mapped_column(server_default=sa.func.now())
    to_date: orm.Mapped[datetime] = orm.mapped_column(server_default=sa.func.now())

    item_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("items.id"))

    item: orm.Mapped["Item"] = orm.relationship()

    @property
    def value(self):
        return self.date.strftime("%d/%m/%Y")

    def __repr__(self):
        return f"<{self.uuid}:{self.value}>"
