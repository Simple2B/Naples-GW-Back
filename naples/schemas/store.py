from pydantic import BaseModel, ConfigDict

from .main_media import MainMedia


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

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreOut(Store):
    main_media: MainMedia | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class Stores(BaseModel):
    stores: list[StoreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
