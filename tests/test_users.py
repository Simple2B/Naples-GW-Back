import base64
from fastapi.testclient import TestClient
from moto import mock_aws
from mypy_boto3_ses import SESClient
import sqlalchemy as sa

from sqlalchemy.orm import Session


from naples import schemas as s
import naples.models as m
from naples.config import config


CFG = config("testing")


def test_get_me(client: TestClient, headers: dict[str, str], test_data: s.TestData):
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    user = s.User.model_validate(response.json())
    assert user.email == test_data.test_users[0].email


def test_get_users(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    test_data: s.TestData,
):
    response = client.get(
        "/api/users/",
        headers=headers,
    )
    assert response.status_code == 200
    users_out = s.Users.model_validate(response.json())
    assert len(users_out.users) == len(test_data.test_users)


def test_update_user(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    test_data: s.TestData,
):
    user = test_data.test_users[0]
    phone = "1234567890"

    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.email == user.email))
    assert db_user

    user_update = s.UserUpdate(
        first_name=user.first_name,
        last_name=user.last_name,
        phone=phone,
    )

    response = client.patch(
        "/api/users/",
        headers=headers,
        json=user_update.model_dump(),
    )

    assert response.status_code == 200

    user_out = s.User.model_validate(response.json())
    assert user_out
    assert user_out.phone == phone

    user_next_update = s.UserUpdate(
        last_name="last_name",
    )

    response = client.patch(
        "/api/users/",
        headers=headers,
        json=user_next_update.model_dump(),
    )

    assert response.status_code == 200

    assert db_user.phone == phone
    assert db_user.last_name == "last_name"
    assert db_user.first_name == user.first_name


@mock_aws
def test_change_password(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    test_data: s.TestData,
    ses: SESClient,
):
    user = test_data.test_users[0]

    ses.verify_email_address(EmailAddress=user.email)
    ses.verify_email_address(EmailAddress=CFG.MAIL_DEFAULT_SENDER)

    data = s.UserResetPasswordIn(
        old_password=user.password,
        new_password="new_password",
    )

    response = client.patch("/api/users/change_password", headers=headers, json=data.model_dump())

    assert response.status_code == 200

    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.email == user.email))
    assert db_user

    assert db_user.password

    change_password = db_user.reset_password_uid
    assert change_password
    db_user.password_hash = change_password

    db.commit()
    db.refresh(db_user)

    credentials = {"username": user.email, "password": data.new_password}
    auth_str = f"{credentials['username']}:{credentials['password']}"
    auth_bytes = base64.b64encode(auth_str.encode())
    auth_header = {"Authorization": f"Basic {auth_bytes.decode()}"}

    response = client.post("/api/auth/login", headers=auth_header)
    assert response.status_code == 200
