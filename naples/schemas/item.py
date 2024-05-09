import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, AliasChoices


from .member import MemberOut
from .fee import FeeOut
from .rate import RateOut
from .floor_plan import FloorPlanOut


class ItemStage(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVE = "archive"


class ItemIn(BaseModel):
    name: str
    description: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    address: str = ""
    size: int = 0
    bedrooms_count: int = 0
    bathrooms_count: int = 0
    city_uuid: str
    realtor_uuid: str
    airbnb_url: str = ""
    vrbo_url: str = ""
    expedia_url: str = ""

    stage: str = ItemStage.DRAFT.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemOut(BaseModel):
    uuid: str
    name: str
    bedrooms_count: int = Field(
        validation_alias=AliasChoices("bedrooms_count", "bedroomsCount"), serialization_alias="bedroomsCount"
    )
    bathroom_count: int = Field(
        validation_alias=AliasChoices("bathrooms_count", "bathroomsCount"), serialization_alias="bathroomsCount"
    )
    size: int
    longitude: float
    latitude: float

    image_url: str = Field("", validation_alias=AliasChoices("image_url", "imageUrl"), serialization_alias="imageUrl")

    stage: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemDetailsOut(ItemOut):
    logo_url: str
    image_url: str
    video_url: str
    realtor: MemberOut
    model_config = ConfigDict(
        from_attributes=True,
    )
    fees: list[FeeOut]
    rates: list[RateOut]
    airbnb_url: str
    vrbo_url: str
    expedia_url: str

    floor_plans: list[FloorPlanOut]

    model_config = ConfigDict(
        from_attributes=True,
    )

    images_urls: list[str] = []

    documents_urls: list[str] = []

    booked_dates: list[datetime] = []


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
    price_max: int
    price_min: int


class ItemDataIn(BaseModel):
    item: ItemIn
