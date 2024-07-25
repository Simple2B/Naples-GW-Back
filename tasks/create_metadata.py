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

        for metadata in s.MetadataType:
            if metadata.value in [data.key for data in metadata_db]:
                log(log.INFO, "This key [%s] already exists ", metadata.value)
            else:
                new_metadata = m.Metadata(key=metadata.value, value="")
                log(log.INFO, "Metada with key [%s] created ", metadata.value)
                session.add(new_metadata)
                session.commit()
