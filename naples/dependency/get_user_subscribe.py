from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from naples import models as m, schemas as s
from naples.database import get_db

from .store import get_current_store
from naples.logger import log


def get_user_subscribe(store: m.Store = Depends(get_current_store), db: Session = Depends(get_db)) -> m.Subscription:
    """Get the current subscription for authorized user.
    Should be used for endpoints related to subscription management by clients."""

    if not store.user.subscription and store.is_protected is False:
        log(log.INFO, "User {%s} does not have a subscription", store.user.uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have a subscription")

    if (
        store.status.value == s.StoreStatus.INACTIVE.value
        and store.user.role != s.UserRole.ADMIN.value
        and store.is_protected is False
    ):
        log(log.INFO, "Store {%s} is inactive", store.uuid)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Subscription is expired")

    return store.user.subscription
