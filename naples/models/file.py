from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import orm

from naples.database import db
from .utils import ModelMixin, create_uuid


class File(db.Model, ModelMixin):
    __tablename__ = "files"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(32), default=create_uuid, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(256), unique=True)

    original_name: orm.Mapped[str] = orm.mapped_column(sa.String(128))

    type: orm.Mapped[str] = orm.mapped_column(sa.String(64))

    url: orm.Mapped[str] = orm.mapped_column(sa.String(512), unique=True)

    s3_url: orm.Mapped[str] = orm.mapped_column(sa.String(512), unique=True)

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    def mark_as_deleted(self):
        delete_date = datetime.now().strftime("%y-%m-%d_%H:%M:%S")
        delete_suffix = f"-deleted-{delete_date}"
        self.is_deleted = True
        self.name = f"{self.name}{delete_suffix}"
        self.url = f"{self.url}{delete_suffix}"

    def __repr__(self):
        return f"<{self.uuid}:{self.name} >"
