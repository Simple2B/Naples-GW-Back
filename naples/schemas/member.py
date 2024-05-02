from pydantic import BaseModel, ConfigDict


class Member(BaseModel):
    name: str
    email: str
    phone: str = ""
    store_id: int
    instagram_url: str = ""
    messenger_url: str = ""
    avatar_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberIn(BaseModel):
    name: str
    email: str
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""
    # avatar_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberOut(Member):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MemberListOut(BaseModel):
    items: list[MemberOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
