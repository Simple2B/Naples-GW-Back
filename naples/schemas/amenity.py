from pydantic import BaseModel, ConfigDict


class AmenityIn(BaseModel):
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AmenityOut(AmenityIn):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AmenitiesListOut(BaseModel):
    items: list[AmenityOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ItemAmenitiesIn(BaseModel):
    amenities_uuids: list[str]

    model_config = ConfigDict(
        from_attributes=True,
    )
