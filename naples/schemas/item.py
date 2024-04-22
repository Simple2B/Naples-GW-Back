import enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ItemStage(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVE = "archive"


class Item(BaseModel):
    name: str
    description: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    store_id: int
    is_deleted: bool = False
    created_at: datetime
    deleted_at: datetime | None = None
    address: str = ""

    stage: str = ItemStage.DRAFT.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemOut(Item):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Items(BaseModel):
    items: list[ItemOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
