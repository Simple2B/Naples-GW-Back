import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from naples import schemas as s
from .utils import ModelMixin, create_uuid


class File(db.Model, ModelMixin):
    __tablename__ = "files"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: create_uuid())

    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        nullable=False,
    )

    original_name: orm.Mapped[str] = orm.mapped_column(
        sa.String(128),
        nullable=False,
    )

    type: orm.Mapped[str] = orm.mapped_column(default=s.FileType.IMAGE.value)

    url: orm.Mapped[str] = orm.mapped_column(sa.String(256), default="")

    # TODO: must be add size of file ?
    # size: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=0)

    owner_type: orm.Mapped[str] = orm.mapped_column(default=s.OwnerType.STORE.value)

    owner_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("users.id"))

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
