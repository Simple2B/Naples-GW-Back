from fastapi import Depends, Form

from sqlalchemy.orm import Session

from naples.database import get_db
import naples.models as m
from naples.logger import log


def get_realtor(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    instagram_url: str = Form(...),
    messenger_url: str = Form(...),
    avatar_url: str = Form(...),
    db: Session = Depends(get_db),
) -> m.Member:
    """Create and then return the current realtor from the database"""
    realtor = m.Member(
        name=name,
        email=email,
        phone=phone,
        instagram_url=instagram_url,
        messenger_url=messenger_url,
        avatar_url=avatar_url,
    )
    db.add(realtor)
    db.flush()
    log(log.INFO, "Realtor [%s] created", realtor.email)
    db.commit()
    return realtor
