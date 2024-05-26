from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BookedDatesBatchIn(BaseModel):
    item_uuid: str
    from_date: datetime
    to_date: datetime


class BookedDateDeleteBatchIn(BaseModel):
    item_uuid: str
    dates_uuids: list[str]


class BookedDateOut(BaseModel):
    uuid: str
    from_date: datetime
    to_date: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class BookedDateListOut(BaseModel):
    items: list[BookedDateOut]
