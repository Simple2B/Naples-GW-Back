from pydantic import BaseModel, ConfigDict, HttpUrl, EmailStr
from pydantic_extra_types.color import Color

from .main_media import MainMedia
from .editable_text import EditableText


class Store(BaseModel):
    logo_url: str = ""
    email: str = ""
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""

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
    instagram_url: HttpUrl | None = None
    messenger_url: HttpUrl | None = None
    phone: str | None = None

    title_value: str | None = None
    title_color: Color | None = None
    title_font_size: int | None = None

    sub_title_value: str | None = None
    sub_title_color: Color | None = None
    sub_title_font_size: int | None = None
    url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreOut(Store):
    url: str
    main_media: MainMedia | None = None

    title: EditableText
    sub_title: EditableText

    model_config = ConfigDict(
        from_attributes=True,
    )


class Stores(BaseModel):
    stores: list[StoreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
