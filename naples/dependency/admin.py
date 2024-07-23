from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from naples.dependency.user import get_current_user

import naples.models as m
import naples.schemas as s
from naples.logger import log

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_admin(user: m.User = Depends(get_current_user)) -> m.User:
    """Raises an exception if the current user is not an admin"""

    if not user.role == s.UserRole.ADMIN.value:
        log(log.INFO, "User wasn`t authorized")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User was not authorized",
        )
    return user
