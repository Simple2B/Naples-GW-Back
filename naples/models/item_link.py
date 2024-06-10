import sqlalchemy as sa

from naples.database import db


items_links = sa.Table(
    "items_links",
    db.Model.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("link_id", sa.ForeignKey("links.id")),
    sa.Column("item_id", sa.ForeignKey("items.id")),
)


class ItemLink(db.Model):
    __tablename__ = "items_links"
