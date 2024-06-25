from fastapi import HTTPException, status
import sqlalchemy as sa
from sqlalchemy.orm import Session

import naples.schemas as s
import naples.models as m
from naples.logger import log
from naples.config import config

CFG = config()


def get_user_data(user: m.User) -> s.User:
    """Get user data"""

    user_data = s.User(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        uuid=user.uuid,
        email=user.email,
        is_verified=user.is_verified,
        role=user.role,
        avatar_url=user.avatar.url if user.avatar else "",
        store_url=user.store_url,
        subscription=s.SubscriptionOut(
            uuid=user.subscription.uuid,
            type=user.subscription.type,
            customer_stripe_id=user.subscription.customer_stripe_id,
            status=user.subscription.status,
            start_date=user.subscription.start_date,
            end_date=user.subscription.end_date,
            subscription_stripe_id=user.subscription.subscription_stripe_id,
            stripe_price_id=user.subscription.stripe_price_id,
            subscription_stripe_item_id=user.subscription.subscription_stripe_item_id,
            created_at=user.subscription.created_at,
            canceled_at=user.subscription.canceled_at if user.subscription.canceled_at else None,
        ),
    )

    log(log.INFO, f"User data: {user_data}")

    return s.User.model_validate(user_data)


def check_user_subscription_options(store: m.Store, db: Session) -> m.Subscription:
    """Check user subscription options"""

    items: list[m.Item] = store.items
    active_items: list[m.Item] = store.active_items

    if store.user.subscription.status == s.SubscriptionStatus.TRIALING.value:
        if len(items) > CFG.MAX_ITEMS_TRIALING:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max items limit reached")

        if len(active_items) > CFG.MAX_ACTIVE_ITEMS_TRIALING:
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
