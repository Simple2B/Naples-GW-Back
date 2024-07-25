from typing import Self
from datetime import datetime
from fastapi import status, HTTPException

import sqlalchemy as sa
from sqlalchemy import orm

from naples.hash_utils import make_hash, hash_verify
from naples.database import db
from .utils import ModelMixin, datetime_utc, create_uuid
from naples.logger import log
from naples import schemas as s
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import Store
    from .subscription import Subscription
    from .file import File


class User(db.Model, ModelMixin):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)

    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)

    email: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    phone: orm.Mapped[str] = orm.mapped_column(sa.String(16), default="", server_default="")

    instagram_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="", server_default="")

    messenger_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="", server_default="")

    linkedin_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="", server_default="")

    avatar_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))

    password_hash: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    is_verified: orm.Mapped[bool] = orm.mapped_column(default=False)
    created_at: orm.Mapped[datetime] = orm.mapped_column(default=datetime_utc)

    role: orm.Mapped[str] = orm.mapped_column(default=s.UserRole.USER.value)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    unique_id: orm.Mapped[str] = orm.mapped_column(
        sa.String(36),
        default="",
    )

    reset_password_uid: orm.Mapped[str] = orm.mapped_column(
        sa.String(64),
        default="",
    )

    store: orm.Mapped["Store"] = orm.relationship()

    avatar: orm.Mapped["File"] = orm.relationship()

    subscriptions: orm.Mapped[list["Subscription"]] = orm.relationship(viewonly=True, order_by="asc(Subscription.id)")

    is_blocked: orm.Mapped[bool] = orm.mapped_column(default=False, server_default=sa.false())

    @property
    def subscription(self):
        # get last saved data in subscriptions
        return self.subscriptions[-1] if self.subscriptions else None

    @property
    def customer_stripe_id(self) -> str:
        return self.subscription.customer_stripe_id if self.subscription else ""

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = make_hash(password)

    @classmethod
    def authenticate(
        cls,
        user_id,
        password,
        session: orm.Session | None = None,
    ) -> Self | None:
        if not session:
            session = db.session
        query = cls.select().where((sa.func.lower(cls.email) == sa.func.lower(user_id)))
        assert session
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", user_id)
        elif hash_verify(
            password,
            user.password,
        ):
            if user.is_blocked:
                log(log.INFO, "User is blocked")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Your account is blocked! Contact the support service",
                )
            return user
        return None

    def reset_password(self):
        self.password_hash = ""
        self.reset_password_uid = create_uuid()
        self.save()

    def __repr__(self):
        return f"<{self.id}: {self.email}>"

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar and not self.avatar.is_deleted else ""

    @property
    def json(self):
        u = s.User.model_validate(self)
        return u.model_dump_json()

    @property
    def store_url(self):
        return self.store.url if self.store else ""

    @classmethod
    def get_user_by_email(cls, email: str, session: orm.Session) -> Self:
        query = cls.select().where((sa.func.lower(cls.email) == sa.func.lower(email)))
        assert session
        user = session.scalar(query)
        return user
