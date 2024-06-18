import sqlalchemy as sa  # noqa: F401
from naples import models as m  # noqa: F401
from naples.database import get_db


db = get_db()
session = next(db)
