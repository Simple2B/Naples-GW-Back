import naples.schemas as s
import naples.models as m
from naples.logger import log


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


def get_product_data(product: m.Product) -> s.ProductOut:
    return s.ProductOut(
        uuid=product.uuid,
        type_name=product.type_name,
        amount=product.amount,
        is_deleted=product.is_deleted,
        stripe_product_id=product.stripe_product_id,
        stripe_price_id=product.stripe_price_id,
        created_at=product.created_at,
        max_items=product.max_items,
        max_active_items=product.max_active_items,
        unactive_items=product.unactive_items,
        description=product.description,
        points=product.points,
    )


def get_base_product_data(product: m.Product) -> s.ProductBaseOut:
    return s.ProductBaseOut(
        uuid=product.uuid,
        type_name=product.type_name,
        amount=product.amount,
        is_deleted=product.is_deleted,
        created_at=product.created_at,
        max_items=product.max_items,
        max_active_items=product.max_active_items,
        unactive_items=product.unactive_items,
        description=product.description,
        points=product.points,
    )
