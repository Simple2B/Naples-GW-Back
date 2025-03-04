import sqlalchemy as sa

from naples.database import db


amenities_items = sa.Table(
    "amenities_items",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("amenity_id", sa.ForeignKey("amenities.id")),
    sa.Column("item_id", sa.ForeignKey("items.id")),
)


class AmenityItem(db.Model):
    __tablename__ = "amenities_items"
