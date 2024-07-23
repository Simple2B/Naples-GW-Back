from enum import Enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactRequestStatus(Enum):
    CREATED = "created"
    PROCESSED = "processed"
    REJECTED = "rejected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ContactRequestIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    message: str
    check_in: datetime
    check_out: datetime
    item_uuid: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ContactRequestUpdateIn(BaseModel):
    status: ContactRequestStatus

    model_config = ConfigDict(
        from_attributes=True,
    )


class ContactRequestOut(ContactRequestIn):
    uuid: str
    status: ContactRequestStatus
    created_at: datetime
    item_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ContactRequestListOut(BaseModel):
    items: list[ContactRequestOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
