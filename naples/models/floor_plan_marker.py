from typing import TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db

from .utils import create_uuid

if TYPE_CHECKING:
    from .floor_plan import FloorPlan


class FloorPlanMarker(db.Model):
    __tablename__ = "floor_plan_markers"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)
    x: orm.Mapped[float] = orm.mapped_column()
    y: orm.Mapped[float] = orm.mapped_column()
    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    floor_plan_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("floor_plans.id"))

    floor_plan: orm.Mapped["FloorPlan"] = orm.relationship()

    @property
    def images(self) -> list[str]:
        return []

    def __repr__(self):
        return f"<{self.id}: x-[{self.x}] y-[{self.y}]>"
