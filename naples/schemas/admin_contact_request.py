from enum import Enum

from pydantic import BaseModel, ConfigDict


class AdminContactRequestStatus(Enum):
    CREATED = "created"
    PROCESSED = "processed"
    REJECTED = "rejected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class AdminContactRequestIn(BaseModel):
    name: str
    email: str
    phone: str
    message: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AdminContactRequestUpdateIn(BaseModel):
    status: AdminContactRequestStatus

    model_config = ConfigDict(
        from_attributes=True,
    )


class AdminContactRequestOut(AdminContactRequestIn):
    uuid: str
    status: str
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class AdminContactRequestListOut(BaseModel):
    contact_requests: list[AdminContactRequestOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
