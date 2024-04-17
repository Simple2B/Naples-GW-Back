from typing import Sequence
from fastapi import Depends, APIRouter, status

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user
from naples.database import get_db


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", status_code=status.HTTP_200_OK, response_model=s.User)
def get_current_user_profile(
    current_user: m.User = Depends(get_current_user),
):
    """Returns the current user profile"""

    log(log.INFO, f"User {current_user.username} requested his profile")
    return current_user


@user_router.get("/", status_code=status.HTTP_200_OK, response_model=s.Users)
def get_users(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Returns the users"""

    stmt: Executable = sa.select(m.User)
    db_users: Sequence[m.User] = db.scalars(stmt).all()
    users: list[s.User] = [
        s.User(
            id=user.id,
            uuid=user.uuid,
            username=user.username,
            email=user.email,
            activated=user.activated,
            role=user.role,
        )
        for user in db_users
    ]

    return s.Users(
        users=users,
    )
