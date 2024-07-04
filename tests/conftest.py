import pytest
from datetime import datetime, timedelta, UTC


from typing import Generator
from pathlib import Path
from mypy_boto3_s3 import S3Client
from mypy_boto3_ses import SESClient
from moto import mock_aws
from moto.ses.models import SESBackend
from requests_mock import Mocker

from dotenv import load_dotenv

load_dotenv("tests/test.env")

# ruff: noqa: F401 E402
from sqlalchemy import orm
from fastapi.testclient import TestClient
from naples.main import api
from naples import models as m
from naples import schemas as s

from naples.config import config


CFG = config("testing")


MODULE_PATH = Path(__file__).parent
TEST_CSV_FILE = MODULE_PATH / ".." / "data" / "test_uscities.csv"


@pytest.fixture
def db(test_data: s.TestData) -> Generator[orm.Session, None, None]:
    from naples.database import db, get_db

    # from services.export_usa_locations import export_usa_locations_from_csv_file
    from services.create_test_data import create_item, create_member, create_store, create_test_user

    with db.Session() as session:
        db.Model.metadata.drop_all(bind=session.bind)
        db.Model.metadata.create_all(bind=session.bind)

        for test_user in test_data.test_users:
            user = create_test_user(test_user)
            session.add(user)
            session.commit()

            user_subscription = session.scalar(m.Subscription.select().where(m.Subscription.user_id == user.id))

            if not user_subscription:
                start_date = datetime.now(UTC)
                end_date = start_date + timedelta(days=30)
                subscription = m.Subscription(
                    user_id=user.id,
                    customer_stripe_id=f"cus_{user.id}",
                    start_date=start_date,
                    end_date=end_date,
                )
                session.add(subscription)
                session.commit()

        for test_store in test_data.test_stores:
            store = create_store(test_store)
            session.add(store)

        # export_usa_locations_from_csv_file(session, TEST_CSV_FILE)

        for test_item in test_data.test_items:
            # city = session.scalars(m.City.select()).all()[0]
            item = create_item(test_item)
            session.add(item)
            location: m.Location = m.Location(
                item_id=test_item.id,
                city=test_item.city,
                state=test_item.state,
                address=test_item.address,
            )
            session.add(location)
            session.commit()
        for member in test_data.test_members:
            new_member = create_member(member)
            session.add(new_member)

        session.commit()

        def override_get_db() -> Generator:
            yield session

        api.dependency_overrides[get_db] = override_get_db
        yield session
        # clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def full_db(db: orm.Session) -> Generator[orm.Session, None, None]:
    yield db


@pytest.fixture
def client(db, requests_mock: Mocker) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""
    with TestClient(api) as c:
        stores = db.scalars(m.Store.select())

        # Mock requests
        requests_mock.get(
            f"{CFG.GODADDY_API_URL}/domains/{CFG.MAIN_DOMAIN}/records",
            json=[
                {
                    "type": "A",
                    "name": store.uuid,
                    "data": "00.000.000.000",
                    "ttl": 600,
                }
                for store in stores
            ],
        )

        requests_mock.patch(f"{CFG.GODADDY_API_URL}/domains/{CFG.MAIN_DOMAIN}/records", json={"status_code": 200})

        for email in ["doe@mail.com", "test_2@mail.com", "test_3@mail.com"]:
            requests_mock.get(
                f"https://api.stripe.com/v1/customers?email={email}",
                json={
                    "object": "list",
                    "url": "/v1/customers",
                    "has_more": False,
                    "data": [
                        {
                            "id": "cus_NffrFeUfNV2Hib",
                            "object": "customer",
                            "address": None,
                            "balance": 0,
                            "created": 1680893993,
                            "currency": None,
                            "default_source": None,
                            "delinquent": False,
                            "description": None,
                            "discount": None,
                            "email": f"{email}",
                            "invoice_prefix": "0759376C",
                            "invoice_settings": {
                                "custom_fields": None,
                                "default_payment_method": None,
                                "footer": None,
                                "rendering_options": None,
                            },
                            "livemode": False,
                            "metadata": {},
                            "name": "Jenny Rosen",
                            "next_invoice_sequence": 1,
                            "phone": None,
                            "preferred_locales": [],
                            "shipping": None,
                            "tax_exempt": "none",
                            "test_clock": None,
                        }
                    ],
                },
            )

        requests_mock.get(
            "https://api.stripe.com/v1/products?active=true",
            json={
                "object": "list",
                "url": "/v1/products",
                "has_more": False,
                "data": [
                    {
                        "id": "prod_NWjs8kKbJWmuuc",
                        "object": "product",
                        "active": True,
                        "created": 1678833149,
                        "default_price": None,
                        "description": None,
                        "images": [],
                        "features": [],
                        "livemode": False,
                        "metadata": {},
                        "name": "Gold Plan",
                        "package_dimensions": None,
                        "shippable": None,
                        "statement_descriptor": None,
                        "tax_code": None,
                        "unit_label": None,
                        "updated": 1678833149,
                        "url": None,
                    }
                ],
            },
        )

        requests_mock.post(
            "https://api.stripe.com/v1/products",
            json={
                "id": "prod_NWjs8kKbJWmuuc",
                "object": "product",
                "active": True,
                "created": 1678833149,
                "default_price": "price_1PNL6qI7HDNT50q3WYkKCTGz",
                "description": "description",
                "images": [],
                "features": [],
                "livemode": False,
                "metadata": None,
                "name": "test product",
                "package_dimensions": None,
                "shippable": None,
                "statement_descriptor": None,
                "tax_code": None,
                "unit_label": None,
                "updated": 1678833149,
                "url": None,
            },
        )

        # subscription_stripe_id = "sub_1PWKkCI7HDNT50q3w1u0yh6x"
        # requests_mock.get(
        #     f"https://api.stripe.com/v1/subscriptions?id={subscription_stripe_id}",
        #     json={
        #         "object": "list",
        #         "url": "/v1/subscriptions",
        #         "has_more": False,
        #         "data": {
        #             "id": "sub_1PWKkCI7HDNT50q3w1u0yh6x",
        #             "object": "subscription",
        #             "application": None,
        #             "application_fee_percent": None,
        #             "automatic_tax": {"enabled": False, "liability": None},
        #             "billing_cycle_anchor": 1679609767,
        #             "billing_thresholds": None,
        #             "cancel_at": None,
        #             "cancel_at_period_end": False,
        #             "canceled_at": None,
        #             "cancellation_details": {
        #                 "comment": None,
        #                 "feedback": None,
        #                 "reason": None,
        #             },
        #             "collection_method": "charge_automatically",
        #             "created": 1679609767,
        #             "currency": "usd",
        #             "current_period_end": 1682288167,
        #             "current_period_start": 1679609767,
        #             "customer": "cus_Na6dX7aXxi11N4",
        #             "days_until_due": None,
        #             "default_payment_method": None,
        #             "default_source": None,
        #             "default_tax_rates": [],
        #             "description": None,
        #             "discount": None,
        #             "discounts": None,
        #             "ended_at": None,
        #             "invoice_settings": {"issuer": {"type": "self"}},
        #             "items": {
        #                 "object": "list",
        #                 "data": [
        #                     {
        #                         "id": "si_Na6dzxczY5fwHx",
        #                         "object": "subscription_item",
        #                         "billing_thresholds": None,
        #                         "created": 1679609768,
        #                         "metadata": {},
        #                         "plan": {
        #                             "id": "price_1POJ3eI7HDNT50q3Efh2O1S7",
        #                             "object": "plan",
        #                             "active": True,
        #                             "aggregate_usage": None,
        #                             "amount": 1000,
        #                             "amount_decimal": "1000",
        #                             "billing_scheme": "per_unit",
        #                             "created": 1679609766,
        #                             "currency": "usd",
        #                             "discounts": None,
        #                             "interval": "month",
        #                             "interval_count": 1,
        #                             "livemode": False,
        #                             "metadata": {},
        #                             "nickname": None,
        #                             "product": "prod_Na6dGcTsmU0I4R",
        #                             "tiers_mode": None,
        #                             "transform_usage": None,
        #                             "trial_period_days": None,
        #                             "usage_type": "licensed",
        #                         },
        #                         "price": {
        #                             "id": "price_1MowQULkdIwHu7ixraBm864M",
        #                             "object": "price",
        #                             "active": True,
        #                             "billing_scheme": "per_unit",
        #                             "created": 1679609766,
        #                             "currency": "usd",
        #                             "custom_unit_amount": None,
        #                             "livemode": False,
        #                             "lookup_key": None,
        #                             "metadata": {},
        #                             "nickname": None,
        #                             "product": "prod_Na6dGcTsmU0I4R",
        #                             "recurring": {
        #                                 "aggregate_usage": None,
        #                                 "interval": "month",
        #                                 "interval_count": 1,
        #                                 "trial_period_days": None,
        #                                 "usage_type": "licensed",
        #                             },
        #                             "tax_behavior": "unspecified",
        #                             "tiers_mode": None,
        #                             "transform_quantity": None,
        #                             "type": "recurring",
        #                             "unit_amount": 1000,
        #                             "unit_amount_decimal": "1000",
        #                         },
        #                         "quantity": 1,
        #                         "subscription": "sub_1MowQVLkdIwHu7ixeRlqHVzs",
        #                         "tax_rates": [],
        #                     }
        #                 ],
        #                 "has_more": False,
        #                 "total_count": 1,
        #                 "url": "/v1/subscription_items?subscription=sub_1MowQVLkdIwHu7ixeRlqHVzs",
        #             },
        #             "latest_invoice": "in_1MowQWLkdIwHu7ixuzkSPfKd",
        #             "livemode": False,
        #             "metadata": {},
        #             "next_pending_invoice_item_invoice": None,
        #             "on_behalf_of": None,
        #             "pause_collection": None,
        #             "payment_settings": {
        #                 "payment_method_options": None,
        #                 "payment_method_types": None,
        #                 "save_default_payment_method": "off",
        #             },
        #             "pending_invoice_item_interval": None,
        #             "pending_setup_intent": None,
        #             "pending_update": None,
        #             "schedule": None,
        #             "start_date": 1679609767,
        #             "status": "active",
        #             "test_clock": None,
        #             "transfer_data": None,
        #             "trial_end": None,
        #             "trial_settings": {"end_behavior": {"missing_payment_method": "create_invoice"}},
        #             "trial_start": None,
        #         },
        #     },
        # )

        yield c


@pytest.fixture
def s3_client() -> Generator[S3Client, None, None]:
    """Returns a mock S3 client"""

    with mock_aws():
        from naples.dependency.s3_client import get_s3_connect
        from naples.config import config

        CFG = config()

        client = get_s3_connect()
        client.create_bucket(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": CFG.AWS_REGION},
        )

        yield client


@mock_aws
@pytest.fixture
def ses() -> Generator[SESClient, None, None]:
    with mock_aws():
        from naples.dependency.ses_client import get_ses_client

        ses = get_ses_client()

    yield ses


@pytest.fixture(scope="session")
def test_data() -> Generator[s.TestData, None, None]:
    """Returns a TestData object"""
    with open("data/test_data.json", "r") as f:
        yield s.TestData.model_validate_json(f.read())


@pytest.fixture
def headers(
    client: TestClient,
    test_data: s.TestData,
) -> Generator[dict[str, str], None, None]:
    """Returns an authorized test client for the API"""
    from naples.oauth2 import create_access_token
    from naples.database import db

    # get user from db
    with db.Session() as session:
        user = session.scalar(m.User.select().where(m.User.email == test_data.test_users[0].email))
        assert user, "User not found"

    token = create_access_token(user_id=user.id)

    yield dict(Authorization=f"Bearer {token}")


@pytest.fixture
def admin_headers(
    client: TestClient,
    test_data: s.TestData,
) -> Generator[dict[str, str], None, None]:
    """Returns an authorized test client admin for the API"""
    from naples.oauth2 import create_access_token
    from naples.database import db

    # get admin from db
    with db.Session() as session:
        user = session.scalar(m.User.select().where(m.User.role == s.UserRole.ADMIN.value))
        assert user, "Admin not found"
    token = create_access_token(user_id=user.id)

    yield dict(Authorization=f"Bearer {token}")
