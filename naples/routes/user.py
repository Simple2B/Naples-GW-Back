from typing import Sequence
from fastapi import Depends, UploadFile, APIRouter, status
from mypy_boto3_s3 import S3Client
from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient


from naples.dependency.get_user_store import get_current_user_store
from naples.hash_utils import make_hash
from naples import controllers as c, models as m, schemas as s

from naples.oauth2 import create_access_token, verify_access_token, HTTPException
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user, get_s3_connect, get_ses_client
from naples.routes.utils import get_user_data
from naples.utils import get_file_extension
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


@user_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=s.User,
)
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

    users: list[s.User] = [get_user_data(user) for user in db_users]

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


@user_router.post(
    "/{user_uuid}/avatar",
    response_model=s.User,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_403_FORBIDDEN: {"description": "User not found"},
    },
)
def upload_user_avatar(
    user_uuid: str,
    avatar: UploadFile,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Uploads the user avatar"""
    log(log.INFO, "Uploading avatar for member {%s} in store {%s}", user_uuid, current_store.uuid)

    user_db = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))

    if not user_db:
        log(log.ERROR, "Member not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_db.store.id != current_store.id:
        log(log.ERROR, "User not found")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")

    extension = get_file_extension(avatar)

    if user_db.avatar:
        log(log.INFO, "Deleting old avatar for member {%s}", user_uuid)
        user_db.avatar.mark_as_deleted()
        db.commit()

    log(log.INFO, "Creating new avatar for member {%s}", user_uuid)

    file_model = c.create_file(
        file=avatar,
        db=db,
        s3_client=s3_client,
        file_type=s.FileType.AVATAR,
        store_url=current_store.url,
        extension=extension,
    )

    user_db.avatar_id = file_model.id
    db.commit()
    db.refresh(user_db)

    log(log.INFO, "Avatar uploaded for member {%s}", user_uuid)

    user = get_user_data(user_db)
    return user


@user_router.delete(
    "/{user_uuid}/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User does not have an avatar"},
        status.HTTP_403_FORBIDDEN: {"description": "User not found"},
        status.HTTP_404_NOT_FOUND: {"description": "User does not have an avatar"},
    },
)
def delete_user_avatar(
    user_uuid: str,
    current_store: m.User = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    """Deletes the user avatar"""
    log(log.INFO, "Deleting avatar for member {%s} in store {%s}", user_uuid, current_store.uuid)

    user = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))

    if not user:
        log(log.ERROR, "User not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.store.id != current_store.id:
        log(log.ERROR, "User not found")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")

    if not user.avatar:
        log(log.ERROR, "User does not have an avatar")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have an avatar")

    user.avatar.mark_as_deleted()
    db.commit()

    log(log.INFO, "Avatar deleted for member {%s}", user_uuid)


@user_router.patch(
    "/change_password",
    status_code=status.HTTP_200_OK,
    response_model=s.User,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Old password is incorrect"},
        status.HTTP_400_BAD_REQUEST: {"description": "Email not sent!"},
    },
)
def change_user_password(
    data: s.UserResetPasswordIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
    ses: SESClient = Depends(get_ses_client),
):
    """Changes the user password"""

    user = m.User.authenticate(current_user.email, data.old_password, session=db)

    if not user:
        log(log.ERROR, f"User {current_user.email} entered wrong old password")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Old password is incorrect")

    user.is_verified = False
    user.password = data.new_password

    log(log.INFO, f"User {current_user.email} changed his password, verification required")

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
            mail_subject=CFG.MAIL_SUBJECT_CHANGE_PASSWORD,
        )
        sendEmailAmazonSES(emailContent, ses_client=ses)

    except ClientError as e:
        log(log.ERROR, f"Email not sent! {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not sent!")

    return current_user


@user_router.get(
    "/change-password/{token}",
    status_code=status.HTTP_200_OK,
    response_model=s.User,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid token"},
    },
)
def save_user_new_password(
    token: str,
    db: Session = Depends(get_db),
):
    """Saves the new password after the user has changed it"""

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

    user.is_verified = True

    db.commit()
    db.refresh(user)

    log(log.INFO, f"User {user.email} changed his password")

    return user


@user_router.post(
    "/forgot_password",
    status_code=status.HTTP_201_CREATED,
    response_model=s.User,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Email not sent!"},
    },
)
def forgot_password(
    data: s.UserForgotPasswordIn,
    db: Session = Depends(get_db),
    ses: SESClient = Depends(get_ses_client),
):
    """Forgot password"""

    user = db.scalar(
        sa.select(m.User).where(
            m.User.email == data.email,
            m.User.is_deleted == sa.false(),
        )
    )

    if not user:
        log(log.ERROR, f"User {data.email} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    token = s.Token(access_token=create_access_token(user.id))

    msg = createMsgEmailChangePassword(token.access_token, CFG.REDIRECT_ROUTER_FORGOT_PASSWORD)

    try:
        emailContent = s.EmailAmazonSESContent(
            recipient_email=user.email,
            sender_email=CFG.MAIL_DEFAULT_SENDER,
            message=msg,
            charset=CFG.CHARSET,
            mail_body_text="Click the link to change your password!",
            mail_subject="Reset your password",
        )
        sendEmailAmazonSES(emailContent, ses_client=ses)

    except ClientError as e:
        log(log.ERROR, f"Email not sent! {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not sent!")

    log(log.INFO, f"User {user.email} forgot his password")

    return user


@user_router.post(
    "/forgot_password/create",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Email not sent!"},
    },
)
def forgot_password_create(
    data: s.UserCreatePasswordIn,
    db: Session = Depends(get_db),
    ses: SESClient = Depends(get_ses_client),
):
    """Create new password when user forgot password"""

    log(log.INFO, "User forgot password")

    token_data: s.TokenData = verify_access_token(data.token, INVALID_CREDENTIALS_EXCEPTION)

    user = db.scalar(
        sa.select(m.User).where(
            m.User.id == token_data.user_id,
            m.User.is_deleted == sa.false(),
        )
    )

    if not user:
        log(log.ERROR, "User not found")
        raise Exception("User not found")

    hashed_password = make_hash(data.password)
    user.password_hash = hashed_password

    db.commit()
    db.refresh(user)

    log(log.INFO, f"User {user.email} changed his password")

    return
