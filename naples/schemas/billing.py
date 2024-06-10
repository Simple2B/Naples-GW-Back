import enum
from pydantic import BaseModel, ConfigDict
from naples.config import config

CFG = config()


class SubscriptionType(enum.Enum):
    TRIALING = "trialing"
    STARTER = "starter"
    PLUS = "plus"
    PRO = "pro"


class SubscriptionProductPricesOut(BaseModel):
    starter_price_id: str
    plus_price_id: str
    pro_price_id: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SubscriptionIn(BaseModel):
    subscription_type: str
    product_price_id: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CheckoutSessionOut(BaseModel):
    id: str
    url: str

    model_config = ConfigDict(arbitrary_types_allowed=True)
