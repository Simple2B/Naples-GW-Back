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
    from .city import City
    from .amenity import Amenity
    from .fee import Fee
    from .rate import Rate
    from .floor_plan import FloorPlan
    from .file import File
    from .booked_date import BookedDate


class Item(db.Model, ModelMixin):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)
    deleted_at: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )
    description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")
    latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)
    longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    address: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    stage: orm.Mapped[str] = orm.mapped_column(default=s.ItemStage.DRAFT.value)
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )
    size: orm.Mapped[int] = orm.mapped_column(default=0)
    bedrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)
    bathrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)
    airbnb_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    vrbo_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    expedia_url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")
    adults: orm.Mapped[int] = orm.mapped_column(default=0, server_default="0")

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))
    city_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("cities.id"))
    realtor_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("members.id"))
    image_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))
    video_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))

    realtor: orm.Mapped["Member"] = orm.relationship()
    store: orm.Mapped["Store"] = orm.relationship()
    city: orm.Mapped["City"] = orm.relationship()

    _amenities: orm.Mapped[list["Amenity"]] = orm.relationship(secondary="amenities_items")
    _fees: orm.Mapped[list["Fee"]] = orm.relationship()
    _rates: orm.Mapped[list["Rate"]] = orm.relationship(back_populates="item")
    _floor_plans: orm.Mapped[list["FloorPlan"]] = orm.relationship(viewonly=True)
    _booked_dates: orm.Mapped[list["BookedDate"]] = orm.relationship(viewonly=True)
    _image: orm.Mapped["File"] = orm.relationship(foreign_keys=[image_id])
    _video: orm.Mapped["File"] = orm.relationship(foreign_keys=[video_id])
    _images: orm.Mapped[list["File"]] = orm.relationship(secondary="items_images")
    _documents: orm.Mapped[list["File"]] = orm.relationship(secondary="items_documents")

    @property
    def amenities(self) -> list[str]:
        return [a.value for a in self._amenities if not a.is_deleted]

    @property
    def fees(self) -> list["Fee"]:
        return [f for f in self._fees if not f.is_deleted]

    @property
    def rates(self) -> list["Rate"]:
        return [r for r in self._rates if not r.is_deleted]

    @property
    def floor_plans(self) -> list["FloorPlan"]:
        return [f for f in self._floor_plans if not f.is_deleted]

    @property
    def image(self):
        return self._image if self._image and not self._image.is_deleted else None

    @property
    def video(self):
        return self._video if self._video and not self._video.is_deleted else None

    @property
    def main_media(self):
        return self.video or self.image

    @property
    def images(self):
        return [i for i in self._images if not i.is_deleted]

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
    def logo_url(self) -> str:
        return self.store.logo_url

    @property
    def image_url(self) -> str:
        return self.image.url if self.image else ""

    @property
    def video_url(self) -> str:
        return self.video.url if self.video else ""

    @property
    def min_price(self) -> float:
        return min([r.night for r in self.rates]) if self.rates else 0

    @property
    def max_price(self) -> float:
        return max([r.month for r in self.rates]) if self.rates else 0

    @property
    def booked_dates(self) -> list[datetime]:
        return [b.date for b in self._booked_dates if not b.is_deleted]

    @property
    def external_urls(self) -> s.ExternalUrls:
        return s.ExternalUrls(
            airbnb_url=self.airbnb_url,
            vrbo_url=self.vrbo_url,
            expedia_url=self.expedia_url,
        )

    def get_fee_by_uuid(self, fee_uuid: str):
        return next((f for f in self.fees if f.uuid == fee_uuid), None)

    def mark_as_deleted(self):
        self.is_deleted = True
        self.deleted_at = datetime_utc()

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
