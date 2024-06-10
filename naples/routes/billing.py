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
from naples.routes.utils import create_stripe_customer


billing_router = APIRouter(prefix="/billings", tags=["Billings"])

CFG = config()


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
        stripe_user = create_stripe_customer(current_user)

        product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == data.stripe_price_id))

        if not product_db:
            log(log.ERROR, "Product not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

        subscription_type = product_db.type_name

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
                "price": data.stripe_price_id,
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

    if not checkout_session.url:
        log(log.ERROR, "User not created in stripe")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

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

        product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

        if not product_db:
            log(log.ERROR, "Product not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

        subscription_type = product_db.type_name

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

            product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

            if not product_db:
                log(log.ERROR, "Product not found")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

            subscription_type = product_db.type_name

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
