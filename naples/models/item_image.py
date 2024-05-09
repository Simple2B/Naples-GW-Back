import sqlalchemy as sa

from naples.database import db


items_images = sa.Table(
    "items_images",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("file_id", sa.ForeignKey("files.id")),
    sa.Column("item_id", sa.ForeignKey("items.id")),
)


class ItemImage(db.Model):
    __tablename__ = "items_images"
