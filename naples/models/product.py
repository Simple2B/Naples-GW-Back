from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from typing import TYPE_CHECKING


from naples.database import db

from .utils import ModelMixin, create_uuid, datetime_utc

if TYPE_CHECKING:
    from .point import Point


class Product(db.Model, ModelMixin):
    __tablename__ = "products"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    type_name: orm.Mapped[str] = orm.mapped_column(default="")

    description: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False, default="")

    amount: orm.Mapped[int] = orm.mapped_column(nullable=False, default=0)

    currency: orm.Mapped[str] = orm.mapped_column(sa.String(8), nullable=False, default="usd")

    recurring_interval: orm.Mapped[str] = orm.mapped_column(sa.String(32), nullable=False, default="month")

    stripe_product_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    stripe_price_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    is_delete: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    _points: orm.Mapped[list["Point"]] = orm.relationship("Point", back_populates="product")

    @property
    def points(self):
        return [point.text for point in self._points]

    def __repr__(self):
        return f"<{self.id}: {self.uuid}>"
