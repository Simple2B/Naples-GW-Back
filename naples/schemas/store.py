import enum
from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic_extra_types.color import Color

from naples.schemas.user import UserOutAdmin

from .main_media import MainMedia
from .editable_text import EditableText


class Store(BaseModel):
    logo_url: str = ""
    email: str = ""
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""
    is_protected: bool = False

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreIn(BaseModel):
    url: str = ""
    email: str
    instagram_url: str = ""
    messenger_url: str = ""
    phone: str = ""

    title_value: str = ""
    title_color: str = ""
    title_font_size: int = 0

    sub_title_value: str = ""
    sub_title_color: str = ""
    sub_title_font_size: int = 0

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreUpdateIn(BaseModel):
    email: EmailStr | None = None
    instagram_url: str | None = None
    messenger_url: str | None = None
    phone: str | None = None

    title_value: str | None = None
    title_color: Color | None = None
    title_font_size: int | None = None

    sub_title_value: str | None = None
    sub_title_color: Color | None = None
    sub_title_font_size: int | None = None
    url: str | None = None

    about_us_description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreAboutUsDescription(BaseModel):
    about_us_description: str = ""


class StoreAboutUs(StoreAboutUsDescription):
    about_us_main_media: MainMedia | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreOut(Store):
    url: str
    main_media: MainMedia | None = None

    title: EditableText
    sub_title: EditableText

    about_us: StoreAboutUs

    model_config = ConfigDict(
        from_attributes=True,
    )


class Stores(BaseModel):
    stores: list[StoreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class StoreAdminOut(BaseModel):
    url: str
    items_count: int
    status: StoreStatus

    user: UserOutAdmin

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoresAdminOut(BaseModel):
    stores: list[StoreAdminOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
