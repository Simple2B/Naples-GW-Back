import sys
from invoke import task
import sqlalchemy as sa


sys.path = ["", ".."] + sys.path[1:]

from naples.database import db  # noqa: E402
from naples import schemas as s, models as m  # noqa: E402
from naples.logger import log  # noqa: E402


@task
def create_metadata(with_print: bool = True):
    with db.Session() as session:
        # get metadatd db
        metadata_db = session.scalars(sa.select(m.Metadata)).all()

        for data in metadata_db:
            if s.MetadataType(data.key):
                log(log.INFO, "This key [%s] already exists ", data.value)
                return
        for metadata in s.MetadataType:
            new_metadata = m.Metadata(key=metadata.value, value="")
            log(log.INFO, "Metada with key [%s] created ", metadata.value)

            session.add(new_metadata)
        session.commit()
