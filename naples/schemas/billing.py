import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from naples.config import config

CFG = config()


class SubscriptionType(enum.Enum):
    TRIALING = "trialing"
    STARTER = "starter"
    PLUS = "plus"
    PRO = "pro"


class Billing(BaseModel):
    uuid: str
    type: str = ""
    customer_stripe_id: str = ""
    subscription_id: str = ""
    subscription_start_date: datetime | None
    subscription_end_date: datetime | None
    subscription_status: str = ""

    stripe_price_id: str = ""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class SubscriptionIn(BaseModel):
    stripe_price_id: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class CheckoutSessionOut(BaseModel):
    id: str
    url: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
