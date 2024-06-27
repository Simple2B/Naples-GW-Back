import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from naples.config import config

CFG = config()


class SubscriptionStatus(enum.Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    # trial perid in our case is 14 days and manege by Fast API
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


# STRIPE SUBSCRIPTION STATUS
# For collection_method=charge_automatically a subscription moves into incomplete if the initial payment attempt fails. A subscription in this status can only have metadata and default_source updated. Once the first invoice is paid, the subscription moves into an active status. If the first invoice is not paid within 23 hours, the subscription transitions to incomplete_expired. This is a terminal status, the open invoice will be voided and no further invoices will be generated.

# A subscription that is currently in a trial period is trialing and moves to active when the trial period is over.

# A subscription can only enter a paused status when a trial ends without a payment method. A paused subscription doesn’t generate invoices and can be resumed after your customer adds their payment method. The paused status is different from pausing collection, which still generates invoices and leaves the subscription’s status unchanged.

# If subscription collection_method=charge_automatically, it becomes past_due when payment is required but cannot be paid (due to failed payment or awaiting additional user actions). Once Stripe has exhausted all payment retry attempts, the subscription will become canceled or unpaid (depending on your subscriptions settings).

# If subscription collection_method=send_invoice it becomes past_due when its invoice is not paid by the due date, and canceled or unpaid if it is still not paid by an additional deadline after that. Note that when a subscription has a status of unpaid, no subsequent invoices will be attempted (invoices will be created, but then immediately automatically closed). After receiving updated payment information from a customer, you may choose to reopen and pay their closed invoices.


class Subscription(BaseModel):
    type: str
    customer_stripe_id: str = ""

    status: SubscriptionStatus

    start_date: datetime
    end_date: datetime

    subscription_stripe_id: str = ""

    stripe_price_id: str = ""

    subscription_stripe_item_id: str | None

    created_at: datetime
    canceled_at: datetime | None = None
    amount: int

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


# info about subscription for admin panel
class SubscriptionOutAdmin(BaseModel):
    type: str = ""
    status: SubscriptionStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SubscriptionHistoryAdmin(BaseModel):
    type: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime

    amount: int

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
