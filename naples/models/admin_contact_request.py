from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from naples.schemas.admin_contact_request import AdminContactRequestStatus

from .utils import create_uuid, datetime_utc

if TYPE_CHECKING:
    from .user import User


# model for contact request from user to admin
class AdminContactRequest(db.Model):
    __tablename__ = "admin_contact_requests"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64))
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    email: orm.Mapped[str] = orm.mapped_column(sa.String(512))
    phone: orm.Mapped[str] = orm.mapped_column(sa.String(64))
    message: orm.Mapped[str] = orm.mapped_column(sa.Text)

    status: orm.Mapped[str] = orm.mapped_column(default=AdminContactRequestStatus.CREATED.value)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    admin_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    admin: orm.Mapped["User"] = orm.relationship()

    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc, server_default=sa.func.now())

    def __repr__(self):
        return f"<AdminContactRequest [{self.uuid}]: Name - [{self.name}]>"
