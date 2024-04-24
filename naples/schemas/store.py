from pydantic import BaseModel, ConfigDict


class Store(BaseModel):
    name: str
    header: str = ""
    sub_header: str = ""
    url: str = ""
    logo_url: str = ""
    about_us: str = ""
    email: str
    instagram_url: str = ""
    messenger_url: str = ""
    user_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreIn(BaseModel):
    name: str
    header: str = ""
    sub_header: str = ""
    url: str = ""
    logo_url: str = ""
    about_us: str = ""
    email: str
    instagram_url: str = ""
    messenger_url: str = ""

    model_config = ConfigDict(
        from_attributes=True,
    )


class StoreOut(Store):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Stores(BaseModel):
    stores: list[StoreOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
