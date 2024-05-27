from pydantic import BaseModel
from naples.schemas.item import ItemIn
from naples.schemas.store import StoreIn

from naples.schemas.member import MemberIn
from naples.schemas.file import FileOut


class TestUser(BaseModel):
    uuid: str
    first_name: str
    last_name: str
    email: str
    password: str
    role: str


class TestItem(ItemIn):
    city_id: int
    store_id: int
    realtor_id: int
    nightly: bool
    monthly: bool
    annual: bool


class TestStore(StoreIn):
    user_id: int


class TestMember(MemberIn):
    store_id: int


class TestData(BaseModel):
    test_users: list[TestUser]
    test_stores: list[TestStore]
    test_items: list[TestItem]
    test_members: list[TestMember]
    test_files: list[FileOut]
