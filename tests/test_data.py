from pydantic import BaseModel


class TestUser(BaseModel):
    __test__ = False

    email: str
    password: str


class TestData(BaseModel):
    __test__ = False

    test_users: list[TestUser]
