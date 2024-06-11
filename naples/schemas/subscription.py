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
