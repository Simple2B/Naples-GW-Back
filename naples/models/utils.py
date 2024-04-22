from datetime import datetime, UTC

from naples.database import db


class ModelMixin(object):
    def save(self, commit=True):
        # Save this model to the database.
        db.session.add(self)
        if commit:
            db.session.commit()
        return self


# Add your own utility classes and functions here.


def datetime_utc():
    return datetime.now(UTC)
