import enum
from pydantic import BaseModel, ConfigDict


class MetadataType(enum.Enum):
    IMAGE_COVER_URL = "image_cover_url"
    VIDEO_COVER_URL = "video_cover_url"


class Metadata(BaseModel):
    key: str
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetadataIn(BaseModel):
    image_cover_url: str | None = None
    video_cover_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetadataOut(BaseModel):
    image_cover_url: str
    video_cover_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Metadaties(BaseModel):
    metadaties: list[Metadata]

    model_config = ConfigDict(
        from_attributes=True,
    )
