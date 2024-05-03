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


class Item(db.Model, ModelMixin):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        unique=True,
        nullable=False,
    )

    description: orm.Mapped[str] = orm.mapped_column(sa.Text, default="")

    latitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    longitude: orm.Mapped[float] = orm.mapped_column(default=0.0)

    store_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("stores.id"))

    store: orm.Mapped["Store"] = orm.relationship()

    city_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("cities.id"))

    city: orm.Mapped["City"] = orm.relationship()

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        default=datetime_utc,
    )

    deleted_at: orm.Mapped[datetime] = orm.mapped_column(nullable=True)

    address: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    stage: orm.Mapped[str] = orm.mapped_column(default=s.ItemStage.DRAFT.value)
    category: orm.Mapped[str] = orm.mapped_column(default=s.ItemCategories.BUY.value)
    type: orm.Mapped[str] = orm.mapped_column(default=s.ItemTypes.HOUSE.value)

    size: orm.Mapped[int] = orm.mapped_column(default=0)
    bedrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)
    bathrooms_count: orm.Mapped[int] = orm.mapped_column(default=0)

    price: orm.Mapped[int] = orm.mapped_column()

    realtor_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("members.id"))

    realtor: orm.Mapped["Member"] = orm.relationship()

    _amenities: orm.Mapped[list["Amenity"]] = orm.relationship(secondary="amenities_items")
    _fees: orm.Mapped[list["Fee"]] = orm.relationship()
    _rates: orm.Mapped[list["Rate"]] = orm.relationship()
    _floor_plans: orm.Mapped[list["FloorPlan"]] = orm.relationship(viewonly=True)

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
    def image_url(self) -> str:
        return ""

    def get_fee_by_uuid(self, fee_uuid: str):
        return next((f for f in self.fees if f.uuid == fee_uuid), None)

    def mark_as_deleted(self):
        self.is_deleted = True
        self.deleted_at = datetime_utc()

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
