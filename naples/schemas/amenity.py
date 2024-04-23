from pydantic import BaseModel, ConfigDict


class Amenity(BaseModel):
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AmenityOut(Amenity):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Amenities(BaseModel):
    amenities: list[AmenityOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
