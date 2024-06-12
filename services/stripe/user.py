import stripe

from fastapi import HTTPException, status

import naples.schemas as s
from naples.config import config
from naples.logger import log


CFG = config()


def create_stripe_customer(current_user: s.User) -> stripe.Customer:
    """Create a stripe customer"""
    stripe.api_key = CFG.STRIPE_SECRET_KEY

    # check user in stripe with this email
    stripe_user = stripe.Customer.list(email=current_user.email)

    if stripe_user:
        log(log.INFO, "User already exists in stripe")
        return stripe_user.data[0]

    create_stripe_user = stripe.Customer.create(email=current_user.email)

    if not create_stripe_user:
        log(log.ERROR, "User not created in stripe")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not created in stripe")

    return create_stripe_user
