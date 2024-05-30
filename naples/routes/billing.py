import stripe

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
from naples.dependency.user import get_current_user
from naples import schemas as s, models as m
from naples.config import config
from naples.logger import log


billing_router = APIRouter(prefix="/billings", tags=["Billings"])

CFG = config()


@billing_router.get("/products", response_model=s.SubscriptionProductPricesOut, status_code=status.HTTP_200_OK)
def get_products_prices(
    current_user: m.User = Depends(get_current_user),
):
    """Get products prices"""

    prices_ids = s.SubscriptionProductPricesOut(
        starter_price_id=CFG.STRIPE_PRICE_STARTER_ID,
        plus_price_id=CFG.STRIPE_PRICE_PLUS_ID,
        pro_price_id=CFG.STRIPE_PRICE_PRO_ID,
    )

    log(log.INFO, "User [%s] get products prices", current_user.email)

    return prices_ids


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

        user_billing = m.Billing(
            user_id=current_user.id,
            customer_stripe_id=stripe_user.id,
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
    )

    log(log.INFO, "User [%s] create checkout session", current_user.email)

    return s.CheckoutSessionOut(
        id=checkout_session.id,
        url=checkout_session.url,
    )


# create portal
@billing_router.post(
    "/create-portal-session",
    response_model=s.CheckoutSessionOut,
    status_code=status.HTTP_200_OK,
)
def create_portal_session(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a portal session"""

    session = stripe.billing_portal.Session.create(
        customer=current_user.stripe_id,
        return_url=CFG.REDIRECT_URL,
    )

    log(log.INFO, "User [%s] create portal session", current_user.email)

    return s.CheckoutSessionOut(
        id=session.id,
        url=session.url,
    )
