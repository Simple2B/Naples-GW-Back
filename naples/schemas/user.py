import enum
from pydantic import BaseModel, ConfigDict


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    id: int
    uuid: str
    email: str
    is_verified: bool = True
    role: str = UserRole.USER.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class Users(BaseModel):
    users: list[User]

    model_config = ConfigDict(
        from_attributes=True,
    )
