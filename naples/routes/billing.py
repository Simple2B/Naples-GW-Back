import stripe
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
from naples.dependency.user import get_current_user
from naples import schemas as s, models as m
from naples.config import config
from naples.logger import log


billing_router = APIRouter(prefix="/billings", tags=["Billings"])

CFG = config()


subscriptionPriceType = {
    CFG.STRIPE_PRICE_STARTER_ID: s.SubscriptionType.STARTER.value,
    CFG.STRIPE_PRICE_PLUS_ID: s.SubscriptionType.PLUS.value,
    CFG.STRIPE_PRICE_PRO_ID: s.SubscriptionType.PRO.value,
}


# @billing_router.get("/products", response_model=s.SubscriptionProductPricesOut, status_code=status.HTTP_200_OK)
# def get_products_prices(
#     current_user: m.User = Depends(get_current_user),
# ):
#     """Get products prices"""

#     prices_ids = s.SubscriptionProductPricesOut(
#         starter_price_id=CFG.STRIPE_PRICE_STARTER_ID,
#         plus_price_id=CFG.STRIPE_PRICE_PLUS_ID,
#         pro_price_id=CFG.STRIPE_PRICE_PRO_ID,
#     )

#     log(log.INFO, "User [%s] get products prices", current_user.email)

#     return prices_ids


@billing_router.post(
    "/create-checkout-session",
    response_model=s.CheckoutSessionOut,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "User not created in stripe"},
    },
)
def create_checkout_session(
    data: s.SubscriptionIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a checkout session"""

    user_billing = db.scalar(sa.select(m.Billing).where(m.Billing.user_id == current_user.id))

    if not user_billing:
        stripe_user = stripe.Customer.create(email=current_user.email)

        if not stripe_user:
            log(log.ERROR, "User not created in stripe")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

        subscription_type = data.subscription_type

        user_billing = m.Billing(
            user_id=current_user.id,
            customer_stripe_id=stripe_user.id,
            type=subscription_type,
        )

        db.add(user_billing)
        db.commit()
        db.refresh(user_billing)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": data.product_price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        customer=user_billing.customer_stripe_id,
        success_url=f"{CFG.REDIRECT_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{CFG.REDIRECT_URL}/cancel",
        subscription_data={
            "trial_period_days": CFG.STRIPE_SUBSCRIPTION_TRIAL_PERIOD_DAYS,
            # TODO: add billing cycle anchor (if needed)
            # "billing_cycle_anchor": 1672531200,
        },
    )

    return s.CheckoutSessionOut(
        id=checkout_session.id,
        url=checkout_session.url,
    )


# create portal
@billing_router.post(
    "/create-portal-session",
    response_model=s.CheckoutSessionOut,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "User not create portal session"},
    },
)
def create_portal_session(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a portal session"""

    session = stripe.billing_portal.Session.create(
        customer=current_user.billing.customer_stripe_id,
        return_url=CFG.REDIRECT_URL,
    )

    if not session:
        log(log.ERROR, "User [%s] not create portal session", current_user.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not create portal session")

    log(log.INFO, "User [%s] create portal session", current_user.email)

    return s.CheckoutSessionOut(
        id=session.id,
        url=session.url,
    )


@billing_router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error verifying webhook signature"},
    },
)
async def webhook_received(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    webhook_secret = CFG.STRIPE_WEBHOOK_KEY

    data = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=data,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )

        event_data = event["data"]

        log(log.INFO, "Webhook received: %s", event_data)

    except Exception as e:
        log(log.ERROR, "Error verifying webhook signature: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error verifying webhook signature")

    event_type = event["type"]
    if event_type == "checkout.session.completed":
        session = event_data["object"]
        log(log.INFO, "Checkout session [%s] completed", session["id"])

    elif event_type == "invoice.paid":
        invoice = event_data["object"]
        log(log.INFO, "Invoice [%s] paid ", invoice["id"])

    elif event_type == "invoice.payment_failed":
        invoice = event_data["object"]
        log(log.INFO, "Invoice payment failed: %s", invoice["id"])

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice payment failed")

    elif event_type == "customer.subscription.deleted":
        subscription = event_data["object"]

        db_billing = db.scalar(sa.select(m.Billing).where(m.Billing.customer_stripe_id == subscription["customer"]))

        if not db_billing:
            log(log.ERROR, "User not found")
            return

        db.delete(db_billing)
        db.commit()

        log(log.INFO, "User subscription deleted")

    elif event_type == "customer.subscription.updated":
        subscription = event_data["object"]

        db_billing = db.scalar(sa.select(m.Billing).where(m.Billing.customer_stripe_id == subscription["customer"]))

        if not db_billing:
            log(log.ERROR, "User not found")
            return

        product_price = subscription["plan"]["id"]
        subscription_type = subscriptionPriceType[product_price]

        stripe.Subscription.modify(
            db_billing.subscription_id,
            items=[
                {"id": subscription["items"]["data"][0].id, "price": product_price},
            ],
        )

        log(log.INFO, "Subscription item id from db: => %s", db_billing.subscription_item_id)

        db_billing.subscription_item_id = subscription["items"]["data"][0].id

        db_billing.amount = subscription["plan"]["amount"] / 100
        db_billing.subscription_status = subscription["status"]
        db_billing.subscription_end_date = datetime.fromtimestamp(subscription["current_period_end"])
        db_billing.subscription_start_date = datetime.fromtimestamp(subscription["current_period_start"])

        db_billing.type = subscription_type

        db.commit()
        db.refresh(db_billing)

        log(log.INFO, "User [%s] subscription updated", db_billing)

    elif event_type == "customer.subscription.created":
        subscription = event_data["object"]

        list = stripe.Subscription.list(customer=subscription["customer"])

        log(log.INFO, " customer for create subscription: %s", list)  # list.data

        db_billing = db.scalar(sa.select(m.Billing).where(m.Billing.customer_stripe_id == subscription["customer"]))

        if not db_billing:
            log(log.ERROR, "User not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

        if not db_billing.subscription_id:
            db_billing.subscription_id = subscription["id"]

            db_billing.amount = subscription["plan"]["amount"] / 100

            sub_item_id = subscription["items"]["data"][0]["id"]
            db_billing.subscription_item_id = sub_item_id

            product_price = subscription["plan"]["id"]
            subscription_type = subscriptionPriceType[product_price]

            db_billing.subscription_status = subscription["status"]

            current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
            db_billing.subscription_start_date = current_period_start

            current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            db_billing.subscription_end_date = current_period_end

            db_billing.type = subscription_type

            db.commit()
            db.refresh(db_billing)

            log(log.INFO, "!!! User [%s] subscription created", db_billing)

    elif event_type == "customer.subscription.trial_will_end":
        subscription = event_data["object"]

        log(log.INFO, "Subscription trial will end: %s", subscription)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription trial will end")

    else:
        log(log.INFO, "Event not handled: %s", event_type)

    return


@billing_router.post(
    "/modify-subscription",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "User not created in stripe"},
    },
)
def modify_subscription(
    data: s.SubscriptionIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Modify subscription"""

    user_billing = db.scalar(sa.select(m.Billing).where(m.Billing.user_id == current_user.id))

    if not user_billing:
        stripe_user = stripe.Customer.create(email=current_user.email)

        if not stripe_user:
            log(log.ERROR, "User not created in stripe")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

        subscription_type = data.subscription_type

        user_billing = m.Billing(
            user_id=current_user.id,
            customer_stripe_id=stripe_user.id,
            type=subscription_type,
        )

        db.add(user_billing)
        db.commit()
        db.refresh(user_billing)

    user_subscription = stripe.Subscription.retrieve(user_billing.subscription_id)

    res = stripe.Subscription.modify(
        user_subscription.id,
        items=[
            {"id": user_subscription.items.data[0].id, "price": data.product_price_id},
        ],
    )

    res

    return
