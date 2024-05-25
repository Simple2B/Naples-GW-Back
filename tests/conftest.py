import pytest


from typing import Generator
from pathlib import Path
from mypy_boto3_s3 import S3Client
from mypy_boto3_ses import SESClient
from moto import mock_aws
from moto.ses.models import SESBackend


from dotenv import load_dotenv


load_dotenv("tests/test.env")

# ruff: noqa: F401 E402
from sqlalchemy import orm
from fastapi.testclient import TestClient
from naples.main import api
from naples import models as m
from naples import schemas as s


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

        for test_store in test_data.test_stores:
            store = create_store(test_store)
            session.add(store)

        export_usa_locations_from_csv_file(session, TEST_CSV_FILE)

        for test_item in test_data.test_items:
            item = create_item(test_item, city_id=test_item.city_id)
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
def client(db) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""
    with TestClient(api) as c:
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


# @pytest.fixture
# def test_send_email(mocker):
#     """Function to test  email sending function"""

#     # mock the smtplib.SMTP object
#     mock_SMTP = mocker.MagicMock(name="your_module.smtplib.SMTP")
#     mocker.patch("your_module.smtplib.SMTP", new=mock_SMTP)

#     #  send email function
#     sendEmailVerify("token", "user@mail.com")

#     assert mock_SMTP.return_value.send_message.call_count == 1
