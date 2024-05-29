from typing import Sequence
from fastapi import Depends, APIRouter, status
from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient

from naples.dependency.ses_client import get_ses_client
from naples.hash_utils import make_hash
import naples.models as m
from naples.oauth2 import create_access_token, verify_access_token, HTTPException
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user
from naples.database import get_db
from naples.utils import createMsgEmailChangePassword, sendEmailAmazonSES
from naples.config import config

CFG = config()

INVALID_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


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
    ses: SESClient = Depends(get_ses_client),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Old password is incorrect"},
        status.HTTP_400_BAD_REQUEST: {"description": "Email not sent!"},
    },
):
    """Resets the user password"""

    user = m.User.authenticate(current_user.email, data.old_password, session=db)

    if not user:
        log(log.ERROR, f"User {current_user.email} entered wrong old password")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old password is incorrect")

    hashed_password = make_hash(data.new_password)

    current_user.reset_password_uid = hashed_password

    db.commit()
    db.refresh(current_user)

    token = s.Token(access_token=create_access_token(current_user.id))

    msg = createMsgEmailChangePassword(token.access_token, CFG.REDIRECT_ROUTER_CHANGE_PASSWORD)

    try:
        emailContent = s.EmailAmazonSESContent(
            recipient_email=current_user.email,
            sender_email=CFG.MAIL_DEFAULT_SENDER,
            message=msg,
            charset=CFG.CHARSET,
            mail_body_text=CFG.MAIL_BODY_TEXT,
            mail_subject=CFG.MAIL_SUBJECT,
        )
        sendEmailAmazonSES(emailContent, ses_client=ses)

    except ClientError as e:
        log(log.ERROR, f"Email not sent! {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not sent!")

    log(log.INFO, f"User {current_user.email} changed his password")

    return current_user


@user_router.get(
    "/change-password/{token}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid token"},
    },
)
def save_new_password(
    token: str,
    db: Session = Depends(get_db),
):
    """Saves the new password"""

    token_data: s.TokenData = verify_access_token(token, INVALID_CREDENTIALS_EXCEPTION)

    user = db.scalar(
        sa.select(m.User).where(
            m.User.id == token_data.user_id,
            m.User.is_deleted == sa.false(),
        )
    )

    if not user:
        log(log.ERROR, "User not found")
        raise Exception("User not found")

    user.password = user.reset_password_uid
    user.reset_password_uid = ""

    db.commit()
    db.refresh(user)

    log(log.INFO, f"User {user.email} saved his new password")

    return
