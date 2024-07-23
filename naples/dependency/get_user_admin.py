from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db

import naples.models as m
import naples.schemas as s
from naples.logger import log


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_user_admin(db: Session = Depends(get_db)) -> m.User:
    """Get the admin user from the database"""
    # TODO: for the feature we may be need to take the super admin from the database instead of the admin

    user = db.scalar(
        sa.select(m.User).where(
            m.User.role == s.UserRole.ADMIN.value,
        )
    )

    if not user:
        log(log.INFO, "Admin not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )

    return user
