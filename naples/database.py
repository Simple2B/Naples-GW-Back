from typing import Generator

from alchemical import Alchemical
from sqlalchemy.orm import Session
from .config import config

CFG = config()


db = Alchemical()
db.initialize(url=CFG.ALCHEMICAL_DATABASE_URL)


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session
