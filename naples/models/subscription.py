from datetime import datetime
import stripe

import sqlalchemy as sa
from sqlalchemy import orm

from typing import TYPE_CHECKING

from naples.database import db
from .utils import ModelMixin, create_uuid, datetime_utc

if TYPE_CHECKING:
    from .user import User


class Subscription(db.Model, ModelMixin):
    __tablename__ = "subscriptions"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    status: orm.Mapped[str] = orm.mapped_column(sa.String(32), default="")

    start_date: orm.Mapped[datetime] = orm.mapped_column(nullable=True)
    end_date: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    stripe_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")
    stripe_item_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    user: orm.Mapped["User"] = orm.relationship()

    @property
    def stripe_price_id(self):
        if self.stripe_id:
            res = stripe.Subscription.retrieve(self.stripe_id)
            return res["items"]["data"][0]["price"]["id"]
        return ""

    def __repr__(self):
        return f"<{self.id}: {self.uuid}>"
