from pydantic import BaseModel, ConfigDict
from datetime import datetime


class BaseRate(BaseModel):
    startDate: datetime
    endDate: datetime
    night: float
    weekendNight: float
    week: float
    month: float
    minStay: int


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
