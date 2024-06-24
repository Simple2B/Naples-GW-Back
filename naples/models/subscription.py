from datetime import datetime
import stripe

import sqlalchemy as sa
from sqlalchemy import orm

from typing import TYPE_CHECKING

from naples.database import db
from naples import schemas as s
from .utils import ModelMixin, create_uuid, datetime_utc

if TYPE_CHECKING:
    from .user import User


class Subscription(db.Model, ModelMixin):
    __tablename__ = "subscriptions"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    type: orm.Mapped[str] = orm.mapped_column(default="")

    status: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=s.SubscriptionStatus.TRIALING.value)

    start_date: orm.Mapped[datetime | None] = orm.mapped_column()
    end_date: orm.Mapped[datetime | None] = orm.mapped_column()

    subscription_stripe_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    subscription_stripe_item_id: orm.Mapped[str | None] = orm.mapped_column(sa.String(128))

    customer_stripe_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    canceled_at: orm.Mapped[datetime | None] = orm.mapped_column()

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    user: orm.Mapped["User"] = orm.relationship()

    last_checked_date: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc, server_default=sa.func.now())

    @property
    def stripe_price_id(self):
        if self.subscription_stripe_id:
            res = stripe.Subscription.retrieve(self.subscription_stripe_id)
            return res["items"]["data"][0]["price"]["id"]
        return ""

    def __repr__(self):
        return f"<{self.id}: {self.uuid}>"
