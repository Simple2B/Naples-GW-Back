from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from datetime import datetime


class BaseRate(BaseModel):
    start_date: datetime = Field(
        serialization_alias="startDate", validation_alias=AliasChoices("start_date", "startDate")
    )
    end_date: datetime = Field(serialization_alias="endDate", validation_alias=AliasChoices("end_date", "endDate"))
    night: float
    weekend_night: float = Field(
        serialization_alias="weekendNight", validation_alias=AliasChoices("weekend_night", "weekendNight")
    )
    week: float
    month: float
    min_stay: int = Field(serialization_alias="minStay", validation_alias=AliasChoices("min_stay", "minStay"))
    visible: bool


class RateIn(BaseRate):
    item_uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateOut(BaseRate):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class RateListOut(BaseModel):
    items: list[RateOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
