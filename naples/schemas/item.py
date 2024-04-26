import enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .member import MemberIn
from .file import FileOut


class ItemTypes(enum.Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    LAND = "land"
    COMMERCIAL = "commercial"


class ItemCategories(enum.Enum):
    BUY = "buy"
    RENT = "rent"


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
    size: int = 0
    bedrooms_count: int = 0
    bathrooms_count: int = 0

    stage: str = ItemStage.DRAFT.value
    category: str = ItemCategories.BUY.value
    type: str = ItemTypes.HOUSE.value

    realtor_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemIn(BaseModel):
    name: str
    description: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    address: str = ""
    size: int = 0
    bedrooms_count: int = 0
    bathrooms_count: int = 0

    stage: str = ItemStage.DRAFT.value
    category: str = ItemCategories.BUY.value
    type: str = ItemTypes.HOUSE.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemRieltorIn(BaseModel):
    item: ItemIn
    rieltor: MemberIn | None = None

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
