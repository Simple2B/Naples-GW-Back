from typing import TYPE_CHECKING
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import create_uuid

if TYPE_CHECKING:
    from .item import Item


class Rate(db.Model):
    __tablename__ = "rates"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)
    start_date: orm.Mapped[datetime] = orm.mapped_column()
    end_date: orm.Mapped[datetime] = orm.mapped_column()
    night: orm.Mapped[float] = orm.mapped_column()
    weekend_night: orm.Mapped[float] = orm.mapped_column()
    week: orm.Mapped[float] = orm.mapped_column()
    month: orm.Mapped[float] = orm.mapped_column()
    min_stay: orm.Mapped[int] = orm.mapped_column()

    visible: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())

    item_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("items.id"))

    item: orm.Mapped["Item"] = orm.relationship()

    @property
    def item_uuid(self):
        return self.item.uuid

    def __repr__(self):
        return f"<{self.id}:{self.start_date.strftime('%d/%b/%Y')} - {self.end_date.strftime('%d/%b/%Y')}>"
