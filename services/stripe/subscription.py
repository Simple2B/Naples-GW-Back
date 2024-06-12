from datetime import datetime
import stripe


from sqlalchemy.orm import Session

import naples.schemas as s
import naples.models as m
from naples.logger import log


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
