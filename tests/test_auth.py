from typing import Sequence

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

new_user_1 = s.UserSignIn(
    first_name=FIRST_USER,
    last_name=LAST_USER,
    email=EMAIL,
    password=PASSWORD,
    role=s.UserRole.USER.value,
)

EMAIL_2 = "test_2@mail.com"
EMAIL_3 = "test_3@mail.com"

new_user_2 = s.UserSignIn(
    first_name=FIRST_USER,
    last_name=LAST_USER,
    email=EMAIL_2,
    password=PASSWORD,
    role=s.UserRole.USER.value,
)

new_user_3 = s.UserSignIn(
    first_name=FIRST_USER,
    last_name=LAST_USER,
    email=EMAIL_3,
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

    response = client.post("/api/auth/sign-up", json=new_user_1.model_dump())
    assert response.status_code == 201
    assert response.json()["email"] == EMAIL
    store = db.scalar(sa.select(m.Store).where(m.Store.email == EMAIL))
    assert store is not None

    ses.verify_email_address(EmailAddress=EMAIL_2)

    response = client.post("/api/auth/sign-up", json=new_user_2.model_dump())
    assert response.status_code == 201
    assert response.json()["email"] == EMAIL_2

    ses.verify_email_address(EmailAddress=EMAIL_3)

    response = client.post("/api/auth/sign-up", json=new_user_3.model_dump())
    assert response.status_code == 201
    assert response.json()["email"] == EMAIL_3

    db_users: Sequence[m.User] = db.scalars(sa.select(m.User)).all()

    assert len(db_users) == 4


@mock_aws
def test_login(
    client: TestClient,
    ses: SESClient,
):
    ses.verify_email_address(EmailAddress=EMAIL)
    ses.verify_email_address(EmailAddress=CFG.MAIL_DEFAULT_SENDER)

    response = client.post("/api/auth/sign-up", json=new_user_1.model_dump())
    assert response.status_code == 201

    form_data = {"username": EMAIL, "password": PASSWORD}

    response = client.post("/api/auth/login", data=form_data)
    assert response.status_code == 200
