import base64

from fastapi.testclient import TestClient


from sqlalchemy.orm import Session
from mypy_boto3_ses import SESClient
from moto import mock_aws

import sqlalchemy as sa

from naples import schemas as s
from naples import models as m

from naples.config import config


CFG = config("testing")

FIRST_USER = "John"
LAST_USER = "Doe"
EMAIL = "doe@mail.com"
PASSWORD = "password"

new_user = s.UserSignIn(
    first_name=FIRST_USER,
    last_name=LAST_USER,
    email=EMAIL,
    password=PASSWORD,
    role=s.UserRole.USER.value,
)


@mock_aws
def test_sign_up(
    client: TestClient,
    db: Session,
    ses: SESClient,
):
    ses.verify_email_address(EmailAddress=EMAIL)
    ses.verify_email_address(EmailAddress=CFG.MAIL_DEFAULT_SENDER)

    response = client.post("/api/auth/sign-up", json=new_user.model_dump())
    assert response.status_code == 201
    assert response.json()["email"] == EMAIL
    store = db.scalar(sa.select(m.Store).where(m.Store.email == EMAIL))
    assert store is not None


@mock_aws
def test_login(
    client: TestClient,
    ses: SESClient,
):
    ses.verify_email_address(EmailAddress=EMAIL)
    ses.verify_email_address(EmailAddress=CFG.MAIL_DEFAULT_SENDER)

    response = client.post("/api/auth/sign-up", json=new_user.model_dump())
    assert response.status_code == 201

    credentials = {"username": EMAIL, "password": PASSWORD}
    auth_str = f"{credentials['username']}:{credentials['password']}"
    auth_bytes = base64.b64encode(auth_str.encode())
    auth_header = {"Authorization": f"Basic {auth_bytes.decode()}"}

    response = client.post("/api/auth/login", headers=auth_header)
    assert response.content is not None
