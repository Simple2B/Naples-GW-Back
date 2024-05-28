import enum
from pydantic import BaseModel, ConfigDict


class MemberType(enum.Enum):
    REALTOR = "realtor"
    OWNER = "owner"
    LANDLORD = "landlord"
    HOST = "host"
    PROPERTY_MANAGER = "property_manager"


class Member(BaseModel):
    name: str
    email: str
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberIn(BaseModel):
    name: str
    email: str
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""
    title: str = MemberType.REALTOR.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberOut(Member):
    uuid: str
    avatar_url: str = ""
    title: MemberType

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberListOut(BaseModel):
    items: list[MemberOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
