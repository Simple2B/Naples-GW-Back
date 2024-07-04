from fastapi import Depends, HTTPException, status

from naples import models as m, schemas as s

from .user import get_current_user
from naples.logger import log


def get_current_user_store(user: m.User = Depends(get_current_user)) -> m.Store:
    """Get the current store for authorized user.
    Should be used for endpoints related to store management by clients.
    Not for public endpoints."""
    if not user.store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have a store")

    if user.store.status.value == s.StoreStatus.INACTIVE.value and user.store.user.role != s.UserRole.ADMIN.value:
        log(log.INFO, "Store {%s} is inactive", user.store.uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subscription is expired")

    return user.store
