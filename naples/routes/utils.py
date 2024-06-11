import stripe

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

import naples.schemas as s
import naples.models as m
from naples.logger import log


def create_stripe_customer(current_user: s.User) -> stripe.Customer:
    """Create a stripe customer"""

    # check user in stripe with this email
    stripe_user = stripe.Customer.list(email=current_user.email)

    if stripe_user:
        log(log.INFO, "User already exists in stripe")
        return stripe_user.data[0]

    create_stripe_user = stripe.Customer.create(email=current_user.email)

    if not create_stripe_user:
        log(log.ERROR, "User not created in stripe")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

    return create_stripe_user


def get_user_subscription(customer_stripe_id: str, db: Session) -> m.Subscription | None:
    """Get user subscription"""

    db_subscription: m.Subscription | None = db.scalar(
        sa.select(m.Subscription).where(m.Subscription.customer_stripe_id == customer_stripe_id)
    )

    return db_subscription


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
            status=user.subscription.status,
            start_date=user.subscription.start_date,
            end_date=user.subscription.end_date,
            subscription_stripe_id=user.subscription.subscription_stripe_id,
            stripe_price_id=user.subscription.stripe_price_id,
        ),
    )

    log(log.INFO, f"User data: {user_data}")

    return s.User.model_validate(user_data)
