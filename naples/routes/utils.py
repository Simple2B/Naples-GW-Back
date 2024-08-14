from datetime import date, datetime, timedelta
from typing import Sequence
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
        role=s.UserRole(user.role),
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
            amount=user.subscription.amount,
        ),
        is_protected=user.is_protected,
    )

    log(log.INFO, f"User data: {user_data}")

    return s.User.model_validate(user_data)


def check_user_subscription_max_items(store: m.Store, db: Session) -> bool:
    """Check user subscription max items"""

    items: list[m.Item] = store.items

    if store.user.subscription.status == s.SubscriptionStatus.TRIALING.value:
        log(log.INFO, f"subscription status: {store.user.subscription.status}")
        if len(items) == CFG.MAX_ITEMS_TRIALING:
            log(log.INFO, f"len items: {len(items)}")
            log(log.INFO, f"Max items limit reached: {CFG.MAX_ITEMS_TRIALING} in trial mode")
            return False
        return True

    stripe_price_id = store.user.subscription.stripe_price_id

    if not stripe_price_id:
        log(log.INFO, "Stripe price id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    product_db: m.Product | None = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == stripe_price_id))

    if not product_db:
        log(log.INFO, "Product not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    max_items = product_db.max_items

    if len(items) == max_items:
        log(log.INFO, f"Max items limit reached: {max_items}")
        return False
    return True


# add only for status item
def check_user_subscription_max_active_items(store: m.Store, item: m.Item, db: Session) -> bool:
    """Check user subscription max active items"""

    active_items: list[m.Item] = store.active_items
    active_items_ids = [i.id for i in active_items]

    if store.user.subscription.status == s.SubscriptionStatus.TRIALING.value:
        if len(active_items) == CFG.MAX_ACTIVE_ITEMS_TRIALING:
            if item.id not in active_items_ids:
                log(log.INFO, f"Max active items limit reached: {CFG.MAX_ACTIVE_ITEMS_TRIALING} in trial mode")
                return False
        return True

    stripe_price_id = store.user.subscription.stripe_price_id
    if not stripe_price_id:
        log(log.INFO, "Stripe price id not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    product_db: m.Product | None = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == stripe_price_id))
    if not product_db:
        log(log.INFO, "Product not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    max_active_items = product_db.max_active_items

    if len(active_items) == max_active_items or len(active_items) > max_active_items:
        if item.id not in active_items_ids:
            log(log.INFO, f"Max active items limit reached: {max_active_items}")
            return False
    return True


# get stores for admin panel
def get_stores_admin(
    db: Session, search: str | None, subscription_status: s.StoreStatus | None
) -> Sequence[s.StoreAdminOut]:
    stmt = sa.select(m.Store)
    stmt_user = sa.select(m.User).where(m.User.is_deleted.is_(False))

    if search:
        stmt_user = sa.select(m.User).where(
            sa.and_(
                m.User.is_deleted.is_(False),
                sa.or_(
                    m.User.email.ilike(f"%{search}%"),
                    m.User.phone.ilike(f"%{search}%"),
                    m.User.first_name.ilike(f"%{search}%"),
                    m.User.last_name.ilike(f"%{search}%"),
                ),
            )
        )

        users_db = db.scalars(stmt_user).all()

        users_ids = [user.id for user in users_db]

        stmt = sa.select(m.Store).where(
            sa.or_(
                m.Store.url.ilike(f"%{search}%"),
                m.Store.user_id.in_(users_ids),
            )
        )

    db_stores = db.scalars(stmt).all()

    today = datetime.now()

    if subscription_status:
        users = db.scalars(stmt_user).all()

        if subscription_status.value == s.StoreStatus.ACTIVE.value:
            users_last_active_subscription = [
                user
                for user in users
                if user.subscription.status == s.SubscriptionStatus.ACTIVE.value
                or (
                    user.subscription.status == s.SubscriptionStatus.TRIALING.value
                    and user.subscription.end_date > today
                )
            ]

            users_ids = [user.id for user in users_last_active_subscription]

            stmt = stmt.where(m.Store.user_id.in_(users_ids))
            db_stores = db.scalars(stmt).all()

        else:
            users_last_active_subscription = [
                user
                for user in users
                if user.subscription.status == s.SubscriptionStatus.CANCELED.value
                or (
                    user.subscription.status != s.SubscriptionStatus.ACTIVE.value and user.subscription.end_date < today
                )
            ]

            users_ids = [user.id for user in users_last_active_subscription]
            stmt = stmt.where(m.Store.user_id.in_(users_ids))
            db_stores = db.scalars(stmt).all()

    stores: Sequence[s.StoreAdminOut] = [s.StoreAdminOut.model_validate(store) for store in db_stores]

    log(log.INFO, "Stores [%s] for admin panel ", len(stores))

    return stores


# create trial subscription
def create_trial_subscription(user: m.User, db: Session, stripe_customer_id: str) -> m.Subscription:
    """Create trial subscription"""

    start_date = datetime.now()
    end_date = start_date + timedelta(days=CFG.STRIPE_SUBSCRIPTION_TRIAL_PERIOD_DAYS)

    user_subscription = m.Subscription(
        user_id=user.id,
        customer_stripe_id=stripe_customer_id,
        start_date=start_date,
        end_date=end_date,
    )

    db.add(user_subscription)
    db.commit()

    log(
        log.INFO,
        "Trial subscription for user [%s] created with trial period [%s]",
        user.email,
        CFG.STRIPE_SUBSCRIPTION_TRIAL_PERIOD_DAYS,
    )

    return user_subscription


# Function to check if date ranges overlap
def is_available(item: s.ItemOut, start_date: date, end_date: date) -> bool:
    for booking in item.booked_dates:
        if not (booking.from_date.date() < start_date or booking.to_date.date() > end_date):
            return False
    return True
