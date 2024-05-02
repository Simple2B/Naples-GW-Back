from typing import TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import create_uuid

if TYPE_CHECKING:
    from .item import Item


class Fee(db.Model):
    __tablename__ = "fees"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())
    name: orm.Mapped[str] = orm.mapped_column(sa.String(128))
    amount: orm.Mapped[float] = orm.mapped_column()
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)
    visible: orm.Mapped[bool] = orm.mapped_column(default=True)

    item_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("items.id"))

    item: orm.Mapped["Item"] = orm.relationship()

    def __repr__(self):
        return f"<{self.id}:{self.name} - {self.amount}>"
