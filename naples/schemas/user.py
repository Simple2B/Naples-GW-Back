import enum
from pydantic import BaseModel, ConfigDict


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    # TODO: Add more roles in the future
    # USER_CREATES = "user_creates"
    # USER_APPROVES = "user_approves"


class User(BaseModel):
    id: int
    uuid: str
    username: str
    email: str
    activated: bool = True
    role: str = UserRole.USER.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class Users(BaseModel):
    users: list[User]

    model_config = ConfigDict(
        from_attributes=True,
    )
