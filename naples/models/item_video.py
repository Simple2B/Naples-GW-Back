import sqlalchemy as sa

from naples.database import db


items_videos = sa.Table(
    "items_videos",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("file_id", sa.ForeignKey("files.id")),
    sa.Column("item_id", sa.ForeignKey("items.id")),
)


class ItemVideo(db.Model):
    __tablename__ = "items_videos"
