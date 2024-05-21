import enum
from pydantic import BaseModel, ConfigDict


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class BaseUser(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: str = UserRole.USER.value

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

    model_config = ConfigDict(
        from_attributes=True,
    )


class Users(BaseModel):
    users: list[User]

    model_config = ConfigDict(
        from_attributes=True,
    )
