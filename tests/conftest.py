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
import stripe

# from unittest.mock import patch
# from services.store.add_dns_record import add_dns_record


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
    from services.export_usa_locations import export_usa_locations_from_csv_file
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
                    status="trial",
                )
                session.add(subscription)
                session.commit()

        for test_store in test_data.test_stores:
            store = create_store(test_store)
            session.add(store)

        export_usa_locations_from_csv_file(session, TEST_CSV_FILE)

        for test_item in test_data.test_items:
            city = session.scalars(m.City.select()).all()[0]
            item = create_item(test_item, city=city)
            session.add(item)
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
            json=[{"name": store.uuid, "type": "A", "ttl": 600, "value": "@"} for store in stores],
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
