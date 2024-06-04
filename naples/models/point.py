from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from typing import TYPE_CHECKING


from naples.database import db
from .utils import ModelMixin, create_uuid, datetime_utc

if TYPE_CHECKING:
    from .product import Product


class Point(db.Model, ModelMixin):
    __tablename__ = "points"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    text: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False, default="")

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    product_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("products.id"))

    product: orm.Mapped["Product"] = orm.relationship()

    def __repr__(self):
        return f"<Point: {self.uuid}>"
