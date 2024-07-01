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
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetadataKeys(BaseModel):
    keys: list[MetadataType]

    model_config = ConfigDict(
        from_attributes=True,
    )


class Metadaties(BaseModel):
    metadaties: list[Metadata]

    model_config = ConfigDict(
        from_attributes=True,
    )
