from pydantic import BaseModel, ConfigDict


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
    logo_url: str = ""
    email: str
    instagram_url: str = ""
    messenger_url: str = ""
    phone: str = ""

    title_value: str = ""
    title_color: str = ""
    title_font_size: int = 24

    sub_title_value: str = ""
    sub_title_color: str = ""
    sub_title_font_size: int = 18

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreOut(Store):
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
