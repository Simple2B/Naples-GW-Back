import sys
from invoke import task


sys.path = ["", ".."] + sys.path[1:]

from naples.config import config  # noqa: E402
from naples.database import db  # noqa: E402
from naples import schemas as s, models as m  # noqa: E402
from naples.logger import log  # noqa: E402

CFG = config()


@task
def create_admin(with_print: bool = True):
    with db.Session() as session:
        if session.query(m.User).filter(m.User.email == CFG.ADMIN_EMAIL).count() > 0:
            log(log.INFO, "Admin user [%s] already exists", CFG.ADMIN_EMAIL)
            return

        admin = m.User(
            first_name=CFG.ADMIN_FIRST_NAME,
            last_name=CFG.ADMIN_LAST_NAME,
            email=CFG.ADMIN_EMAIL,
            password=CFG.ADMIN_PASSWORD,
            role=s.UserRole.ADMIN.value,
            is_verified=True,
        )

        session.add(admin)
        session.commit()

        log(log.INFO, "Admin user [%s] created", CFG.ADMIN_EMAIL)

        return admin
