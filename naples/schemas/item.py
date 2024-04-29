import enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .member import MemberIn


class ItemTypes(enum.Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    LAND = "land"
    COMMERCIAL = "commercial"


class ItemCategories(enum.Enum):
    BUY = "BUY"
    RENT = "RENT"


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
    price: int
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
    price: int
    bedrooms_count: int = 0
    bathrooms_count: int = 0
    city_uuid: str

    stage: str = ItemStage.DRAFT.value
    category: str = ItemCategories.BUY.value
    type: str = ItemTypes.HOUSE.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemRieltorIn(BaseModel):
    item: ItemIn
    realtor: MemberIn | None = None

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


class ItemsFilterDataIn(BaseModel):
    city_uuid: str | None = None
    category: str | None = None
    type: str | None = None
    price_max: int | None = None
    price_min: int | None = None


class ItemsFilterDataOut(BaseModel):
    categories: list[ItemCategories]
    types: list[ItemTypes]
    price_max: int
    price_min: int


class Params(BaseModel):
    page: int = 1
    size: int = 50

    def to_raw_params(self):
        return {
            "limit": self.size if self.size is not None else None,
            "offset": self.size * (self.page - 1) if self.page is not None and self.size is not None else None,
        }
