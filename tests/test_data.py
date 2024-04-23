import uuid
from pydantic import BaseModel


class TestUser(BaseModel):
    __test__ = False

    id: int
    email: str
    password: str


class TestStore(BaseModel):
    __test__ = False

    uuid: str
    name: str
    header: str
    sub_header: str
    url: str
    logo_url: str
    about_us: str
    email: str
    instagram_url: str
    messenger_url: str
    user_id: int


class TestData(BaseModel):
    __test__ = False

    test_users: list[TestUser]
    test_stores: list[TestStore]
