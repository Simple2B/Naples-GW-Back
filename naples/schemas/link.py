import enum
from pydantic import BaseModel, ConfigDict


class LinkType(enum.Enum):
    YouTubeVideo = "youtube"
    YouTuVideo = "youtu.be"
    UNKNOWN = "unknown"


class Link(BaseModel):
    type: str = LinkType.YouTubeVideo.value
    url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LinkIn(BaseModel):
    url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LinkOut(Link):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LinksOut(BaseModel):
    links: list[LinkOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
