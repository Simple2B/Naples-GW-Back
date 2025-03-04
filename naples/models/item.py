from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid, datetime_utc
from naples import schemas as s
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .store import Store
    from .member import Member
    from .amenity import Amenity
    from .fee import Fee
    from .rate import Rate
    from .floor_plan import FloorPlan
    from .file import File
    from .booked_date import BookedDate
    from .contact_request import ContactRequest
    from .link import Link
    from .location import Location


class Item(db.Model, ModelMixin):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)
    deleted_at: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        nullable=False,
    )
    description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")
    # latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)
    # longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    # address: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    stage: orm.Mapped[str] = orm.mapped_column(default=s.ItemStage.DRAFT.value)

    size: orm.Mapped[int] = orm.mapped_column(default=0)
    bedrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)
    bathrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)
    airbnb_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    vrbo_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    expedia_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    adults: orm.Mapped[int] = orm.mapped_column(default=0, server_default="0")
    show_rates: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())
    show_fees: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())
    show_external_urls: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())
    nightly: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())
    monthly: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())
    annual: orm.Mapped[bool] = orm.mapped_column(default=True, server_default=sa.true())

    # store id should not be changed via API
    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    realtor_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("members.id"))

    # media should be changed via separate API endpoints
    main_media_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))

    realtor: orm.Mapped["Member"] = orm.relationship()
    store: orm.Mapped["Store"] = orm.relationship()

    location: orm.Mapped["Location"] = orm.relationship(back_populates="item")

    _amenities: orm.Mapped[list["Amenity"]] = orm.relationship(secondary="amenities_items")
    _fees: orm.Mapped[list["Fee"]] = orm.relationship()
    _rates: orm.Mapped[list["Rate"]] = orm.relationship(back_populates="item")
    _floor_plans: orm.Mapped[list["FloorPlan"]] = orm.relationship(viewonly=True)
    _booked_dates: orm.Mapped[list["BookedDate"]] = orm.relationship(viewonly=True)

    _main_media: orm.Mapped["File"] = orm.relationship()

    _images: orm.Mapped[list["File"]] = orm.relationship(secondary="items_images")

    _documents: orm.Mapped[list["File"]] = orm.relationship(secondary="items_documents")

    _contact_requests: orm.Mapped[list["ContactRequest"]] = orm.relationship(viewonly=True)

    _videos: orm.Mapped[list["File"]] = orm.relationship(secondary="items_videos")

    _links: orm.Mapped[list["Link"]] = orm.relationship(secondary="items_links")

    @property
    def longitude(self):
        return self.location.longitude if self.location else 0.0

    @property
    def latitude(self):
        return self.location.latitude if self.location else 0.0

    @property
    def city(self):
        return self.location.city if self.location else ""

    @property
    def state(self):
        return self.location.state if self.location else ""

    @property
    def address(self):
        return self.location.address if self.location else ""

    @property
    def videos(self):
        return [v for v in self._videos if not v.is_deleted]

    @property
    def links(self):
        return [link for link in self._links if not link.is_deleted]

    @property
    def videos_links(self):
        videos = [
            s.ItemVideoLinkOut(
                url=v.url,
                type=s.ItemVideoLinkType.VIDEO,
                uuid=v.uuid,
            )
            for v in self._videos
            if not v.is_deleted
        ]
        links = [
            s.ItemVideoLinkOut(
                url=link.url,
                type=s.ItemVideoLinkType.YOUTUBE,
                uuid=link.uuid,
            )
            for link in self._links
            if not link.is_deleted
        ]

        return videos + links

    @property
    def amenities(self) -> list[str]:
        return [a.value for a in self._amenities if not a.is_deleted]

    @property
    def fees(self) -> list["Fee"]:
        return [f for f in self._fees if not f.is_deleted] if self._fees else []

    @property
    def rates(self) -> list["Rate"]:
        return [r for r in self._rates if not r.is_deleted] if self._rates else []

    @property
    def floor_plans(self) -> list["FloorPlan"]:
        return [f for f in self._floor_plans if not f.is_deleted]

    @property
    def main_media(self):
        return self._main_media if self._main_media and not self._main_media.is_deleted else None

    @property
    def images(self):
        files_list = [i for i in self._images if not i.is_deleted]
        files_list.sort(key=lambda file: file.updated_at)
        return files_list

    @property
    def images_urls(self) -> list[str]:
        return [i.url for i in self.images]

    @property
    def documents(self):
        return [d for d in self._documents if not d.is_deleted]

    @property
    def documents_urls(self) -> list[str]:
        return [d.url for d in self.documents]

    @property
    def image_url(self) -> str:
        if self.main_media.type == "image":
            return self.main_media.url
        if self.images:
            return self.images[0].url
        return ""

    @property
    def logo_url(self) -> str:
        return self.store.logo_url

    @property
    def min_price(self) -> float:
        return min([r.night for r in self.rates]) if self.rates else 0

    @property
    def max_price(self) -> float:
        return max([r.month for r in self.rates]) if self.rates else 0

    @property
    def booked_dates(self) -> list["BookedDate"]:
        res = [b for b in self._booked_dates if not b.is_deleted]
        return res

    @property
    def external_urls(self) -> s.ExternalUrls:
        return s.ExternalUrls(
            airbnb_url=self.airbnb_url,
            vrbo_url=self.vrbo_url,
            expedia_url=self.expedia_url,
        )

    @property
    def contact_requests(self):
        return [contact_request for contact_request in self._contact_requests if not contact_request.is_deleted]

    def get_fee_by_uuid(self, fee_uuid: str):
        return next((f for f in self.fees if f.uuid == fee_uuid), None)

    def mark_as_deleted(self):
        self.is_deleted = True
        self.deleted_at = datetime_utc()
        if self.main_media:
            self.main_media.mark_as_deleted()
        for image in self.images:
            image.mark_as_deleted()
        for video in self.videos:
            video.mark_as_deleted()

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
