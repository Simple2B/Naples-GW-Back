from datetime import datetime
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


def get_user_last_data_subscription(customer_stripe_id: str, db: Session) -> m.Subscription | None:
    """Get user subscription"""

    result: sa.ScalarResult = db.scalars(
        sa.select(m.Subscription)
        .where(m.Subscription.customer_stripe_id == customer_stripe_id)
        .order_by(sa.desc(m.Subscription.created_at))
    )

    subscriptions = result.all()

    if not subscriptions:
        log(log.INFO, "No subscriptions found")
        return None

    return subscriptions[0]


def get_product_by_id(product_price: str, db: Session) -> s.Product:
    """Get product by id"""

    product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

    if not product_db:
        log(log.ERROR, "Product not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found, please contact support")

    return s.Product.model_validate(product_db)


def save_state_subscription_from_stripe(
    subscription_data: stripe.Subscription, product: s.Product, db: Session
) -> m.Subscription:
    """Save subscription state"""

    user_subscription = m.Subscription(
        customer_stripe_id=subscription_data["customer"],
        subscription_stripe_id=subscription_data["id"],
        status=subscription_data["status"],
        subscription_stripe_item_id=subscription_data["items"]["data"][0]["id"],
        start_date=datetime.fromtimestamp(subscription_data["current_period_start"]),
        end_date=datetime.fromtimestamp(subscription_data["current_period_end"]),
        canceled_at=datetime.fromtimestamp(subscription_data["canceled_at"]),
        type=product.type_name,
        product_price=product.stripe_price_id,
    )

    db.add(user_subscription)
    db.commit()

    log(log.INFO, "Subscription state saved")

    return user_subscription


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
            canceled_at=user.subscription.canceled_at,
        ),
    )

    log(log.INFO, f"User data: {user_data}")

    return s.User.model_validate(user_data)
