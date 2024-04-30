from pydantic import BaseModel
from naples.schemas.item import ItemOut
from naples.schemas.store import StoreOut

from naples.schemas.member import MemberOut


class TestUser(BaseModel):
    id: int
    email: str
    password: str


class TestItem(ItemOut):
    city_id: int


class TestData(BaseModel):
    test_users: list[TestUser]
    test_stores: list[StoreOut]
    test_items: list[TestItem]
    test_members: list[MemberOut]
