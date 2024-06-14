from datetime import datetime, timedelta, UTC
from typing import Annotated
from fastapi import Depends, APIRouter, status, HTTPException
from fastapi.security import HTTPBasic, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import sqlalchemy as sa
from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient
import stripe

from naples.dependency import get_ses_client
from naples.oauth2 import (
    INVALID_CREDENTIALS_EXCEPTION,
    create_access_token,
    create_access_token_exp_datetime,
    verify_access_token,
)
from naples import models as m
from naples import schemas as s
from naples.logger import log
from naples.database import get_db

from naples.utils import createMsgEmail, delete_user_with_store, sendEmailAmazonSES
from naples.config import config
from services.store.add_dns_record import add_dns_record
from services.stripe.product import get_product_by_id
from services.stripe.subscription import save_state_subscription_from_stripe
from services.stripe.user import create_stripe_customer

security = HTTPBasic()

router = APIRouter(prefix="/auth", tags=["Auth"])

CFG = config()


# login router only for swagger for this project, that why include_in_schema is False
@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=s.TokenOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin user can not get API token"},
    },
    include_in_schema=False,
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db=Depends(get_db),
):
    """Logs in a user"""

    user = m.User.authenticate(form_data.username, form_data.password, session=db)

    if not user:
        log(log.ERROR, "User [%s] wrong username (email) or password", form_data.username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.email)

    # update last subscription in db with stripe data every 3 days
    if user.subscription and user.subscription.last_checked_date < datetime.now() - timedelta(
        days=CFG.DAYS_BEFORE_UPDATE
    ):
        stripe_subscription_data = stripe.Subscription.retrieve(user.subscription.subscription_stripe_id)

        product = get_product_by_id(stripe_subscription_data["items"]["data"][0]["plan"]["id"], db)

        save_state_subscription_from_stripe(user.subscription, product, db)

        log(log.INFO, "Subscription state updated for user [%s]", user.email)

    return create_access_token_exp_datetime(user.id)


@router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    response_model=s.TokenOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid credentials"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin user can not get API token"},
        status.HTTP_400_BAD_REQUEST: {"description": "User not verified"},
    },
)
def get_token(auth_data: s.Auth, db=Depends(get_db)):
    """Logs in a user"""
    user = m.User.authenticate(auth_data.email, auth_data.password, session=db)

    if not user:
        log(log.ERROR, "User [%s] wrong email or password", auth_data.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

    if not user.is_verified:
        log(log.ERROR, "User [%s] not verified", auth_data.email)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not verified. Please verify your email"
        )

    # admin user can not get API token
    if user.role == s.UserRole.ADMIN.value:
        log(log.ERROR, "User [%s] is an admin user", user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin user can not get API token")
    log(log.INFO, "User [%s] logged in", user.email)

    return create_access_token_exp_datetime(user.id)


@router.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=s.User,
    responses={
        status.HTTP_409_CONFLICT: {"description": "User already exists"},
        status.HTTP_400_BAD_REQUEST: {"description": "Email not sent!"},
    },
)
def sign_up(
    data: s.UserSignIn,
    db: Session = Depends(get_db),
    ses: SESClient = Depends(get_ses_client),
):
    """Signs up a user"""

    user = m.User.get_user_by_email(data.email, session=db)

    if user:
        log(log.ERROR, "User [%s] already exists", data.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    new_user: m.User = m.User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password=data.password,
    )

    db.add(new_user)
    db.commit()

    log(log.INFO, "User [%s] signed up", new_user.email)

    user_store = m.Store(
        user_id=new_user.id,
        email=new_user.email,
        url=f"{new_user.uuid}.{CFG.MAIN_DOMAIN}",
    )

    db.add(user_store)
    db.commit()

    log(log.INFO, "Store for user [%s] created", new_user.email)

    # add dns for store url
    dns_record = s.DNSRecord(
        domain=CFG.MAIN_DOMAIN,
        subdomain=new_user.uuid,
        record_type=CFG.RECORD_TYPE,
        ttl=CFG.TTL,
        value=CFG.GODADDY_IP_ADDRESS,
        api_url=CFG.GODADDY_API_URL,
        api_key=CFG.GODADDY_API_KEY,
        api_secret=CFG.GODADDY_API_SECRET,
    )

    add_dns_record(dns_record)

    log(log.INFO, "DNS record added for store [%s]", new_user.email)

    # create stripe customer
    stripe_customer = create_stripe_customer(new_user)

    start_date = datetime.now(UTC)
    end_date = start_date + timedelta(days=CFG.STRIPE_SUBSCRIPTION_TRIAL_PERIOD_DAYS)

    # subscription
    user_subscription = m.Subscription(
        user_id=new_user.id,
        customer_stripe_id=stripe_customer.id,
        start_date=start_date,
        end_date=end_date,
        status="trial",
    )

    db.add(user_subscription)
    db.commit()

    log(
        log.INFO,
        "Subscription for user [%s] created with trial period [%s]",
        new_user.email,
        CFG.STRIPE_SUBSCRIPTION_TRIAL_PERIOD_DAYS,
    )

    token = s.Token(access_token=create_access_token(new_user.id))

    msg = createMsgEmail(token.access_token, CFG.REDIRECT_ROUTER_VERIFY_EMAIL)

    try:
        emailContent = s.EmailAmazonSESContent(
            recipient_email=new_user.email,
            sender_email=CFG.MAIL_DEFAULT_SENDER,
            message=msg,
            charset=CFG.CHARSET,
            mail_body_text=CFG.MAIL_BODY_TEXT,
            mail_subject=CFG.MAIL_SUBJECT,
        )
        sendEmailAmazonSES(emailContent, ses_client=ses)

    except ClientError as e:
        delete_user_with_store(db, new_user)

        log(log.ERROR, "Email not sent! [%s]", e)
        log(log.INFO, "User [%s] user is not registered", new_user.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not sent!")

    log(log.INFO, "Verification email sent to [%s]", new_user.email)

    return new_user


@router.get(
    "/verify-email/{token}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Invalid token"},
    },
)
def verify_email(
    token: str,
    db: Session = Depends(get_db),
    ses: SESClient = Depends(get_ses_client),
):
    """Verifies email"""

    token_data: s.TokenData = verify_access_token(token, INVALID_CREDENTIALS_EXCEPTION)

    user = db.scalar(
        sa.select(m.User).where(
            m.User.id == token_data.user_id,
            m.User.is_deleted == sa.false(),
        )
    )

    if not user:
        log(log.ERROR, "User not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    user.is_verified = True
    db.commit()

    log(log.INFO, "User [%s] verified email", user.email)

    return
