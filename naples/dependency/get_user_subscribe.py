from datetime import datetime
from fastapi import Depends, HTTPException, status

from naples import models as m

from .store import get_current_store


def get_user_subscribe(store: m.Store = Depends(get_current_store)) -> m.Subscription:
    """Get the current subscription for authorized user.
    Should be used for endpoints related to subscription management by clients."""

    if not store.user.subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have a subscription")

    if store.user.subscription.status == "canceled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription is canceled")

    date_now = datetime.now()
    if store.user.subscription.end_date < date_now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription is expired")

    return store.user.subscription
