from datetime import datetime, UTC
from uuid import uuid4

from naples.database import db


class ModelMixin(object):
    def save(self, commit=True):
        # Save this model to the database.
        db.session.add(self)
        if commit:
            db.session.commit()
        return self


def datetime_utc():
    return datetime.now(UTC)


def create_uuid():
    return uuid4().hex
