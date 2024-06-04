from datetime import datetime

from pydantic import BaseModel, ConfigDict
from naples.config import config

CFG = config()


class Point(BaseModel):
    text: str
    product_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PointIn(BaseModel):
    text: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class PointOut(Point):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class PointsOut(BaseModel):
    Points: list[PointOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
