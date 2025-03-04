from typing import TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import create_uuid

if TYPE_CHECKING:
    from .item import Item
    from .floor_plan_marker import FloorPlanMarker
    from .file import File


class FloorPlan(db.Model):
    __tablename__ = "floor_plans"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    item_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("items.id"))

    item: orm.Mapped["Item"] = orm.relationship()

    image_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("files.id"))

    _image: orm.Mapped["File"] = orm.relationship("File")

    _markers: orm.Mapped[list["FloorPlanMarker"]] = orm.relationship("FloorPlanMarker", back_populates="floor_plan")

    @property
    def image(self):
        return self._image if self._image and not self._image.is_deleted else None

    @property
    def img_url(self):
        return self.image.url if self.image else ""

    @property
    def markers(self):
        return [marker for marker in self._markers if not marker.is_deleted]

    def __repr__(self):
        return f"<{self.id}:{self.img_url}>"
