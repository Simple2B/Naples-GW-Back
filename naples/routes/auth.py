from typing import Annotated
from fastapi import Depends, APIRouter, status, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from naples.oauth2 import create_access_token
from sqlalchemy.orm import Session
import sqlalchemy as sa


from naples import models as m
from naples import schemas as s
from naples.logger import log
from naples.database import get_db

security = HTTPBasic()

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=s.Token,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin user can not get API token"},
    },
)
def login(credentials: Annotated[HTTPBasicCredentials, Depends(security)], db=Depends(get_db)):
    """Logs in a user"""

    user = m.User.authenticate(credentials.username, credentials.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong username (email) or password", credentials.username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.email)
    return s.Token(access_token=create_access_token(user.id))


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    response_model=s.Token,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin user can not get API token"},
    },
)
def get_token(auth_data: s.Auth, db=Depends(get_db)):
    """Logs in a user"""
    user = m.User.authenticate(auth_data.email, auth_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong email or password", auth_data.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.email)
    return s.Token(access_token=create_access_token(user.id))


@router.post("/sign-up", status_code=status.HTTP_201_CREATED, response_model=s.User)
def sign_up(data: s.UserSignIn, db: Session = Depends(get_db)):
    """Signs up a user"""

    user = m.User.get_user_by_email(data.email, session=db)

    if user:
        log(log.ERROR, "User [%s] already exists", data.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    new_user: m.User = m.User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password=data.password,
    )
    db.add(new_user)
    db.commit()

    log(log.INFO, "User [%s] signed up", new_user.email)

    db_store = db.scalar(sa.select(m.Store).where(m.Store.user_id == new_user.id))

    if not db_store:
        user_store = m.Store(user_id=new_user.id, email=new_user.email)
        db.add(user_store)
        db.commit()
        log(log.INFO, "Store for user [%s] created", new_user.email)

    return new_user
