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

    log(log.INFO, f"User {current_user.email} requested his profile")
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
            first_name=user.first_name,
            last_name=user.last_name,
            uuid=user.uuid,
            email=user.email,
            is_verified=user.is_verified,
            role=user.role,
        )
        for user in db_users
    ]

    return s.Users(
        users=users,
    )


@user_router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.User,
)
def update_user(
    data: s.UserUpdate,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Updates the user"""

    if data.first_name:
        log(log.INFO, f"User {current_user.email} updated his first name to {data.first_name}")
        current_user.first_name = data.first_name

    if data.last_name:
        log(log.INFO, f"User {current_user.email} updated his last name to {data.last_name}")
        current_user.last_name = data.last_name

    if data.phone:
        log(log.INFO, f"User {current_user.email} updated his phone to {data.phone}")
        current_user.phone = data.phone

    db.commit()

    log(log.INFO, f"User {current_user.email} updated his profile")

    return current_user


@user_router.patch(
    "/change_password",
    status_code=status.HTTP_200_OK,
    response_model=s.User,
)
def change_password(
    data: s.UserResetPasswordIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Resets the user password"""

    user = m.User.authenticate(current_user.email, data.old_password, session=db)

    if not user:
        log(log.ERROR, f"User {current_user.email} entered wrong old password")
        raise Exception("Old password is incorrect")

    current_user.password = data.new_password

    db.commit()
    db.refresh(current_user)

    return current_user
