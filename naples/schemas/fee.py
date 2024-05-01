from pydantic import BaseModel


class FeeIn(BaseModel):
    name: str
    amount: float
    visible: bool
    item_uuid: str


class FeeOut(BaseModel):
    uuid: str
    name: str
    amount: float
