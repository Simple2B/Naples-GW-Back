from typing import Annotated
from fastapi import Depends, APIRouter, status, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from naples.oauth2 import create_access_token

from  naples import models as m
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
        log(log.ERROR, "User [%s] wrong username or password", credentials.username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.username)
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
    user = m.User.authenticate(auth_data.username, auth_data.password, session=db)
    if not user:
        log(log.ERROR, "User [%s] wrong username or password", auth_data.username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.username)
    return s.Token(access_token=create_access_token(user.id))
