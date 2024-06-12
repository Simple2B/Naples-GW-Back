from datetime import datetime
from pydantic import BaseModel, ConfigDict
from naples.config import config

CFG = config()


class Subscription(BaseModel):
    type: str = ""
    customer_stripe_id: str = ""

    status: str = ""

    start_date: datetime | None
    end_date: datetime | None

    subscription_stripe_id: str = ""

    stripe_price_id: str = ""

    subscription_stripe_item_id: str | None

    created_at: datetime
    canceled_at: datetime | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class SubscriptionIn(BaseModel):
    stripe_price_id: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class SubscriptionOut(Subscription):
    uuid: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class CheckoutSessionOut(BaseModel):
    id: str
    url: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class StripePlan(BaseModel):
    id: str


class StripeItemData(BaseModel):
    id: str


class StripeItem(BaseModel):
    data: list[StripeItemData]


class StripeObject(BaseModel):
    id: str
    canceled_at: int | None
    currency: str
    current_period_end: int
    current_period_start: int
    customer: str
    items: StripeItem
    status: str
    plan: StripePlan


class StripeObjectSubscription(BaseModel):
    object: StripeObject
