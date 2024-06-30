from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm


from naples.database import db
from naples import schemas as s

from .utils import ModelMixin, create_uuid, datetime_utc


class Product(db.Model, ModelMixin):
    __tablename__ = "products"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    type_name: orm.Mapped[str] = orm.mapped_column(default=s.ProductType.STARTER.value)

    amount: orm.Mapped[int] = orm.mapped_column(nullable=False, default=0)

    currency: orm.Mapped[str] = orm.mapped_column(sa.String(8), nullable=False, default="usd")

    recurring_interval: orm.Mapped[str] = orm.mapped_column(default=s.ProductTypeRecurringInterval.MONTH.value)

    stripe_product_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    stripe_price_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    max_items: orm.Mapped[int] = orm.mapped_column(default=1)
    max_active_items: orm.Mapped[int] = orm.mapped_column(default=1)

    min_items: orm.Mapped[int] = orm.mapped_column(default=1)

    inactive_items: orm.Mapped[int] = orm.mapped_column(default=0)

    @property
    def points(self):
        return [f"Up to {self.max_active_items} active", f"{self.inactive_items} Unactive"]

    @property
    def description(self):
        return f"{self.min_items} - {self.max_active_items} Properties"

    def __repr__(self):
        return f"<{self.id}: {self.uuid}>"
