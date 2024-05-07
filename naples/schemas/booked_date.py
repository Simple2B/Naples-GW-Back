from datetime import datetime
from pydantic import BaseModel


class BookedDatesBatchIn(BaseModel):
    item_uuid: str
    dates: list[datetime]


class BookedDateDeleteBatchIn(BaseModel):
    item_uuid: str
    dates_uuids: list[str]


class BookedDateOut(BaseModel):
    uuid: str
    date: datetime


class BookedDateListOut(BaseModel):
    items: list[BookedDateOut]
