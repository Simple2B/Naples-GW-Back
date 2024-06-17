import enum
from pydantic import BaseModel, ConfigDict, Field, AliasChoices


from .main_media import MainMedia
from .member import MemberOut
from .fee import FeeOut
from .rate import RateOut
from .floor_plan import FloorPlanOut
from .locations import LocationOut, CityOut
from .file import DocumentOut
from .booked_date import BookedDateOut


class ItemStage(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVE = "archive"


class RentalLength(enum.Enum):
    NIGHTLY = "nightly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class ExternalUrls(BaseModel):
    airbnb_url: str
    vrbo_url: str
    expedia_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemIn(BaseModel):
    name: str
    description: str = ""
    address: str = ""
    size: int = 0
    bedrooms_count: int = 0
    bathrooms_count: int = 0
    city_uuid: str
    realtor_uuid: str
    airbnb_url: str = ""
    vrbo_url: str = ""
    expedia_url: str = ""
    adults: int = 0

    stage: str = ItemStage.DRAFT.value

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemUpdateIn(BaseModel):
    name: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    stage: ItemStage | None = None
    size: int | None = None
    bedrooms_count: int | None = None
    bathrooms_count: int | None = None
    airbnb_url: str | None = None
    vrbo_url: str | None = None
    expedia_url: str | None = None
    adults: int | None = None
    city_uuid: str | None = None
    realtor_uuid: str | None = None
    show_rates: bool | None = None
    show_fees: bool | None = None
    show_external_urls: bool | None = None
    nightly: bool | None = None
    monthly: bool | None = None
    annual: bool | None = None

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

    stage: ItemStage

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemVideoLinkType(enum.Enum):
    YOUTUBE = "youtube"
    S3BUCKET = "s3bucket"


class ItemVideoLinkOut(BaseModel):
    uuid: str
    type: ItemVideoLinkType
    url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemDetailsOut(ItemOut):
    logo_url: str
    main_media: MainMedia | None = None
    realtor: MemberOut
    fees: list[FeeOut]
    rates: list[RateOut]
    floor_plans: list[FloorPlanOut]

    model_config = ConfigDict(
        from_attributes=True,
    )

    images_urls: list[str]

    documents: list[DocumentOut]

    booked_dates: list[BookedDateOut]

    videos_links: list[ItemVideoLinkOut]

    description: str
    amenities: list[str]
    external_urls: ExternalUrls
    adults: int
    show_rates: bool
    show_fees: bool
    show_external_urls: bool
    nightly: bool
    monthly: bool
    annual: bool

    city: CityOut


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
    locations: list[LocationOut]
    adults: int


class ItemDataIn(BaseModel):
    item: ItemIn
