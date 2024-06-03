from typing import Sequence
from fastapi import Depends, UploadFile, APIRouter, status
from mypy_boto3_s3 import S3Client
from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient


from naples.controllers.file import get_file_type
from naples.hash_utils import make_hash
from naples import controllers as c, models as m, schemas as s

from naples.oauth2 import create_access_token, verify_access_token, HTTPException
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user, get_s3_connect, get_ses_client
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


@user_router.post(
    "/avatar",
    status_code=status.HTTP_201_CREATED,
    response_model=s.User,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Extension not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "File type not supported"},
    },
)
def upload_avatar(
    avatar: UploadFile,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Uploads the user avatar"""

    log(log.INFO, f"User {current_user.email} uploading avatar")

    if current_user.avatar and not current_user.avatar.is_deleted:
        log(log.INFO, f"User {current_user.email} deleting old avatar")
        current_user.avatar.mark_as_deleted()
        db.commit()

    extension = get_file_extension(avatar)

    if not extension:
        log(log.ERROR, "Extension not found for avatar [%s]", avatar.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    file_type = get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "File type not supported for avatar [%s]", avatar.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not supported")

    avatar_file_model = c.create_file(
        db=db,
        file=avatar,
        s3_client=s3_client,
        extension=extension,
        store_url=current_user.store.url,
        file_type=file_type,
    )

    current_user.avatar_id = avatar_file_model.id
    db.commit()
    db.refresh(current_user)

    log(log.INFO, f"User {current_user.email} uploaded avatar")

    return current_user


@user_router.delete(
    "/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User does not have an avatar"},
    },
)
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Deletes the user avatar"""

    log(log.INFO, f"User {current_user.email} deleting avatar")

    if not current_user.avatar:
        log(log.ERROR, f"User {current_user.email} does not have an avatar")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have an avatar")

    current_user.avatar.mark_as_deleted()
    db.commit()

    log(log.INFO, f"User {current_user.email} deleted avatar")


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
