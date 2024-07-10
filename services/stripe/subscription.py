from fastapi import HTTPException, status
import stripe
from datetime import datetime

from sqlalchemy.orm import Session
import sqlalchemy as sa

import naples.schemas as s
import naples.models as m
from naples.logger import log


def save_state_subscription_from_stripe(
    subscription: stripe.Subscription, product: s.Product, db: Session
) -> m.Subscription:
    """Save subscription state"""

    subscription_data = s.StripeObject(**subscription)

    user_subscriptions = (
        db.execute(sa.select(m.Subscription).where(m.Subscription.customer_stripe_id == subscription_data.customer))
        .scalars()
        .all()
    )

    current_subscription = user_subscriptions[-1] if user_subscriptions else None

    current_user = current_subscription.user if current_subscription else None

    if not current_user:
        # user not found in stripe
        log(log.ERROR, "User not found in stripe")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found in stripe")

    if (
        subscription_data.status == s.SubscriptionStatus.ACTIVE.value
        and current_user.subscription.status == s.SubscriptionStatus.ACTIVE.value
    ):
        current_user.subscription.status = s.SubscriptionStatus.CANCELED.value
        db.commit()
        db.refresh(current_user)

    if (
        subscription_data.status == s.SubscriptionStatus.CANCELED.value
        and current_user.subscription.status == s.SubscriptionStatus.ACTIVE.value
    ):
        current_user.subscription.status = s.SubscriptionStatus.CANCELED.value
        db.commit()
        db.refresh(current_user)
        return current_user.subscription

    user_subscription = m.Subscription(
        customer_stripe_id=subscription_data.customer,
        subscription_stripe_id=subscription_data.id,
        status=subscription_data.status,
        subscription_stripe_item_id=subscription_data.items.data[0].id,
        start_date=datetime.fromtimestamp(subscription_data.current_period_start),
        end_date=datetime.fromtimestamp(subscription_data.current_period_end),
        canceled_at=datetime.fromtimestamp(subscription_data.canceled_at) if subscription_data.canceled_at else None,
        type=product.type_name,
        user_id=current_user.id,
        amount=product.amount,
    )

    db.add(user_subscription)
    db.commit()
    db.refresh(user_subscription)

    log(log.INFO, "Subscription state saved")

    return user_subscription
