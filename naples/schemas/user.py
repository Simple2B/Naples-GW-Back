from datetime import datetime
import enum
from pydantic import BaseModel, ConfigDict
from naples.schemas.subscription import SubscriptionHistoryAdmin, SubscriptionOut, SubscriptionOutAdmin


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class BaseUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    avatar_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserForgotPasswordIn(BaseModel):
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserCreatePasswordIn(BaseModel):
    password: str
    token: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserSignIn(BaseUser):
    password: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class User(BaseUser):
    id: int
    uuid: str
    is_verified: bool = True
    store_url: str

    role: UserRole

    subscription: SubscriptionOut

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserResetPasswordIn(BaseModel):
    old_password: str
    new_password: str


class Users(BaseModel):
    users: list[User]

    model_config = ConfigDict(
        from_attributes=True,
    )


class EmailAmazonSESContent(BaseModel):
    recipient_email: str
    sender_email: str
    message: str = ""
    charset: str = "UTF-8"
    mail_body_text: str = ""
    mail_subject: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)


# info about user for admin panel
class UserOutAdmin(BaseModel):
    uuid: str
    first_name: str
    last_name: str
    email: str
    phone: str
    created_at: datetime
    is_blocked: bool
    role: UserRole

    subscription: SubscriptionOutAdmin

    model_config = ConfigDict(
        from_attributes=True,
    )


# for admin panel
class StoreHistoryAdmin(BaseModel):
    url: str
    items_count: int
    created_at: datetime
    email: str
    phone: str
    instagram_url: str
    messenger_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserSubscriptionHistoryAdmin(BaseModel):
    uuid: str
    first_name: str
    last_name: str

    store: StoreHistoryAdmin

    subscriptions: list[SubscriptionHistoryAdmin]

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserIsBlockedIn(BaseModel):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )
