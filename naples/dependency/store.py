import validators

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
import naples.models as m
from naples.logger import log


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_store(store_url: str | None, db: Session = Depends(get_db)) -> m.Store:
    """Get the current store from the database"""

    if store_url is None:
        log(log.INFO, "Store URL is not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Store URL is not provided",
        )

    if not validators.domain(store_url):
        log(log.INFO, "Invalid URL: %s", store_url)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid URL",
        )

    store = db.scalar(
        sa.select(m.Store).where(
            m.Store.url == store_url,
        )
    )

    if store is None:
        log(log.INFO, "Store not found: %s", store_url)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    if store.user.is_blocked and store.is_protected is False:
        log(log.INFO, "User is blocked")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Your account is blocked! Contact the support service",
        )

    return store
