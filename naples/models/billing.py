from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from typing import TYPE_CHECKING


from naples.database import db
from naples import schemas as s
from .utils import ModelMixin, create_uuid, datetime_utc

if TYPE_CHECKING:
    from .user import User


class Billing(db.Model, ModelMixin):
    __tablename__ = "billings"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    type: orm.Mapped[str] = orm.mapped_column(default="")

    description: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False, default="")

    amount: orm.Mapped[int] = orm.mapped_column(nullable=False, default=0)

    customer_stripe_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    subscription_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    subscription_start_date: orm.Mapped[datetime] = orm.mapped_column(nullable=True)
    subscription_end_date: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    subscription_status: orm.Mapped[str] = orm.mapped_column(sa.String(32), nullable=True)

    subscription_item_id: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    user: orm.Mapped["User"] = orm.relationship()

    def __repr__(self):
        return f"<{self.id}: {self.uuid}>"
