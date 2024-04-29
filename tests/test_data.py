from pydantic import BaseModel
from naples import schemas as s


class TestItem(s.ItemOut):
    __test__ = False

    city_id: int


class TestUser(BaseModel):
    __test__ = False

    id: int
    email: str
    password: str


class TestData(BaseModel):
    __test__ = False

    test_users: list[TestUser]
    test_stores: list[s.StoreOut]
    test_items: list[TestItem]
    test_members: list[s.MemberOut]
