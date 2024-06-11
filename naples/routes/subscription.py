import stripe
from datetime import UTC, datetime, MINYEAR

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
from naples.dependency.user import get_current_user
from naples import schemas as s, models as m
from naples.config import config
from naples.logger import log
from naples.routes.utils import create_stripe_customer, get_user_subscription


subscription_router = APIRouter(prefix="/subscription", tags=["Subscription"])

CFG = config()


@subscription_router.post(
    "/create-checkout-session",
    response_model=s.CheckoutSessionOut,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "User not created in stripe"},
        status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
    },
)
def create_checkout_session(
    data: s.SubscriptionIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a checkout session"""

    product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == data.stripe_price_id))

    if not product_db:
        log(log.ERROR, "Product not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    user_subscription = db.scalar(sa.select(m.Subscription).where(m.Subscription.user_id == current_user.id))

    if not user_subscription:
        stripe_user = create_stripe_customer(current_user)

        subscription_type = product_db.type_name

        user_subscription = m.Subscription(
            user_id=current_user.id,
            customer_stripe_id=stripe_user.id,
            type=subscription_type,
        )

        db.add(user_subscription)
        db.commit()
        db.refresh(user_subscription)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price": data.stripe_price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        customer=user_subscription.customer_stripe_id,
        success_url=f"{CFG.REDIRECT_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{CFG.REDIRECT_URL}/subscription/cancel",
    )

    if not checkout_session.url:
        log(log.ERROR, "User not created in stripe")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

    return s.CheckoutSessionOut(
        id=checkout_session.id,
        url=checkout_session.url,
    )


# create portal
@subscription_router.post(
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


@subscription_router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error verifying webhook signature"},
    },
    include_in_schema=False,
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

    subscription = event_data["object"]

    db_subscription: m.Subscription | None = get_user_subscription(subscription["customer"], db)

    if not db_subscription:
        log(log.ERROR, "User subscription not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User subscription not found")

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
        db_subscription.subscription_stripe_id = ""
        db_subscription.status = ""
        db_subscription.type = ""
        db_subscription.subscription_stripe_item_id = ""
        db_subscription.start_date = datetime(MINYEAR, 1, 1)
        db_subscription.end_date = datetime(MINYEAR, 1, 1)
        db.commit()

        log(log.INFO, "User subscription deleted [%s]", db_subscription.customer_stripe_id)

    elif event_type == "customer.subscription.updated":
        product_price = subscription["plan"]["id"]

        product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

        if not product_db:
            log(log.ERROR, "Product not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

        subscription_type = product_db.type_name

        stripe.Subscription.modify(
            db_subscription.subscription_stripe_id,
            items=[
                {"id": subscription["items"]["data"][0].id, "price": product_price},
            ],
        )

        log(log.INFO, "[stripe] user subscription updated [%s]", db_subscription.customer_stripe_id)

        db_subscription.subscription_stripe_item_id = subscription["items"]["data"][0].id
        db_subscription.status = subscription["status"]
        db_subscription.start_date = datetime.fromtimestamp(subscription["current_period_start"])
        db_subscription.end_date = datetime.fromtimestamp(subscription["current_period_end"])

        db_subscription.type = subscription_type

        db.commit()
        db.refresh(db_subscription)

        log(log.INFO, "[db] user [%s] subscription updated", db_subscription.customer_stripe_id)

    elif event_type == "customer.subscription.created":
        if not db_subscription.subscription_stripe_id:
            db_subscription.subscription_stripe_id = subscription["id"]

            sub_item_id = subscription["items"]["data"][0]["id"]
            db_subscription.subscription_stripe_item_id = sub_item_id

            product_price = subscription["plan"]["id"]

            product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

            if not product_db:
                log(log.ERROR, "Product not found")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")

            subscription_type = product_db.type_name

            db_subscription.status = subscription["status"]

            current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
            db_subscription.start_date = current_period_start

            current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            db_subscription.end_date = current_period_end

            db_subscription.type = subscription_type

            db.commit()
            db.refresh(db_subscription)

            log(log.INFO, "[db] User [%s] subscription created", db_subscription)

    else:
        log(log.INFO, "Event not handled: %s", event_type)

    return


@subscription_router.post(
    "/modify-subscription",
    status_code=status.HTTP_200_OK,
    response_model=s.Subscription,
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

    user_subscription = db.scalar(sa.select(m.Subscription).where(m.Subscription.user_id == current_user.id))

    if not user_subscription:
        log(log.ERROR, "User subscription not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User subscription not found")

    user_stripe_subscription = stripe.Subscription.retrieve(user_subscription.subscription_stripe_id)

    res = stripe.Subscription.modify(
        user_stripe_subscription.id,
        items=[
            {"id": user_subscription.subscription_stripe_item_id, "price": data.stripe_price_id},
        ],
    )

    log(log.INFO, "User subscription modified [%s]", res)

    return user_subscription


# TODO: cancel subscription
# @subscription_router.post(
#     "/cancel-subscription",
#     status_code=status.HTTP_200_OK,
#     response_model=s.Subscription,
#     responses={
#         status.HTTP_400_BAD_REQUEST: {"description": "User not created in stripe"},
#     },
# )
# def cancel_subscription(
#     db: Session = Depends(get_db),
#     current_user: m.User = Depends(get_current_user),
# ):
#     """Cancel subscription"""

#     user_subscription = db.scalar(sa.select(m.Subscription).where(m.Subscription.user_id == current_user.id))

#     if not user_subscription:
#         log(log.ERROR, "User subscription not found")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User subscription not found")

#     user_stripe_subscription = stripe.Subscription.retrieve(user_subscription.subscription_stripe_id)

#     if not user_stripe_subscription:
#         log(log.ERROR, "User stripe subscription not found")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User stripe subscription not found")

#     if user_stripe_subscription.status == "canceled":
#         log(log.INFO, "User subscription already canceled [%s]", user_subscription.customer_stripe_id)
#         return user_subscription

#     res = stripe.Subscription.modify(
#         user_stripe_subscription.id,
#         cancel_at_period_end=True,
#     )

#     log(log.INFO, "User subscription cancelled [%s]", res)

#     if res:
#         user_subscription.subscription_stripe_id = ""
#         user_subscription.status = ""
#         user_subscription.type = ""
#         user_subscription.subscription_stripe_item_id = ""
#         user_subscription.start_date = datetime(MINYEAR, 1, 1)
#         user_subscription.end_date = datetime(MINYEAR, 1, 1)
#         db.commit()

#         log(log.INFO, "User subscription canceled [%s]", user_subscription.customer_stripe_id)

#     return user_subscription
