import enum
from pydantic import BaseModel, ConfigDict


class SubscriptionType(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PLUS = "plus"
    PRO = "pro"


class SubscriptionProductPricesOut(BaseModel):
    starter_price_id: str
    plus_price_id: str
    pro_price_id: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SubscriptionIn(BaseModel):
    product_price_id: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CheckoutSessionOut(BaseModel):
    id: str
    url: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
