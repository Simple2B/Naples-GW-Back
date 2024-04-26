from pydantic import BaseModel
from naples.schemas import store as s


class TestUser(BaseModel):
    __test__ = False

    id: int
    email: str
    password: str


class TestData(BaseModel):
    __test__ = False

    test_users: list[TestUser]
    test_stores: list[s.StoreOut]
