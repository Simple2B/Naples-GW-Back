import enum
from pydantic import BaseModel, ConfigDict


class MetadataType(enum.Enum):
    IMAGE_COVER_URL = "image_cover_url"
    VIDEO_COVER_URL = "video_cover_url"
    CONTACT_PHONE = "contact_phone"
    CONTACT_EMAIL = "contact_email"
    CONTACT_INSTAGRAM_URL = "contact_instagram_url"
    CONTACT_FACEBOOK_URL = "contact_facebook_url"
    CONTACT_LINKEDIN_URL = "contact_linkedin_url"


class Metadata(BaseModel):
    key: str
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetadataIn(BaseModel):
    image_cover_url: str | None = None
    video_cover_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_instagram_url: str | None = None
    contact_facebook_url: str | None = None
    contact_linkedin_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetadataOut(BaseModel):
    image_cover_url: str
    video_cover_url: str
    contact_phone: str
    contact_email: str
    contact_instagram_url: str
    contact_facebook_url: str
    contact_linkedin_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Metadaties(BaseModel):
    metadaties: list[Metadata]

    model_config = ConfigDict(
        from_attributes=True,
    )
