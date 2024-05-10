from typing import Literal
from pydantic import BaseModel, ConfigDict


class MainMedia(BaseModel):
    url: str
    type: Literal["image", "video"]

    model_config = ConfigDict(
        from_attributes=True,
    )
