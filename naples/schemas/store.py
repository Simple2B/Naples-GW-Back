from pydantic import BaseModel, ConfigDict


class Store(BaseModel):
    header: str = ""
    sub_header: str = ""
    logo_url: str = ""
    about_us: str = ""
    email: str
    phone: str = ""
    instagram_url: str = ""
    messenger_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreIn(BaseModel):
    header: str = ""
    sub_header: str = ""
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
    main_image_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class Stores(BaseModel):
    stores: list[StoreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
