from datetime import datetime
from fastapi import Depends, HTTPException, status
import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples import models as m, schemas as s
from naples.database import get_db

from .store import get_current_store

MAX_ITEMS_TRIALING = 5
MAX_ACTIVE_ITEMS_TRIALING = 3


def get_user_subscribe(store: m.Store = Depends(get_current_store), db: Session = Depends(get_db)) -> m.Subscription:
    """Get the current subscription for authorized user.
    Should be used for endpoints related to subscription management by clients."""

    if not store.user.subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have a subscription")

    date_now = datetime.now()
    if store.user.subscription.end_date < date_now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription is expired")

    items: list[m.Item] = store.items
    active_items: list[m.Item] = store.active_items

    if store.user.subscription.status == s.SubscriptionStatus.TRIALING.value:
        if len(items) > MAX_ITEMS_TRIALING:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max items limit reached")

        if len(active_items) > MAX_ACTIVE_ITEMS_TRIALING:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max active items limit reached")

        return store.user.subscription

    stripe_price_id = store.user.subscription.stripe_price_id
    if not stripe_price_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    product_db: m.Product | None = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == stripe_price_id))
    if not product_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    max_active_items = product_db.max_active_items
    max_items = product_db.max_items

    if len(items) > max_items:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max items limit reached")

    if len(active_items) > max_active_items:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max active items limit reached")

    return store.user.subscription
