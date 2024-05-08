import sqlalchemy as sa

from naples.database import db


floor_plan_markers_images = sa.Table(
    "floor_plan_markers_images",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("file_id", sa.ForeignKey("files.id")),
    sa.Column("floor_plan_marker_id", sa.ForeignKey("floor_plan_markers.id")),
)


class FloorPlanMarkerImage(db.Model):
    __tablename__ = "floor_plan_markers_images"
