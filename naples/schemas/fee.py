from pydantic import BaseModel, ConfigDict


class FeeIn(BaseModel):
    name: str
    amount: float
    visible: bool
    item_uuid: str


class FeeOut(BaseModel):
    uuid: str
    name: str
    amount: float
    visible: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class FeeListOut(BaseModel):
    items: list[FeeOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
