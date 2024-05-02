from fastapi import Depends, HTTPException, status

from naples import models as m

from .user import get_current_user


def get_current_user_store(user: m.User = Depends(get_current_user)) -> m.Store:
    """Get the current store for authorized user.
    Should be used for endpoints related to store management by clients.
    Not for public endpoints."""
    if not user.store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have a store")
    return user.store
