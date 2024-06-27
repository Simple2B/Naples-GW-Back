from fastapi.testclient import TestClient
from moto import mock_aws
from mypy_boto3_s3 import S3Client
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


def test_upload_avatar(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        user_model = full_db.scalar(sa.select(m.User))
        assert user_model

        response = client.post(
            f"/api/users/{user_model.uuid}/avatar",
            headers=headers,
            files={"avatar": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        user_res = client.get("/api/users/me", headers=headers)
        assert user_res.status_code == 200

        user = s.User.model_validate(user_res.json())

        assert user.avatar_url and user.avatar_url == user_model.avatar.url

        full_db.refresh(user_model)

        bucket_file = s3_client.get_object(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            Key=user_model.avatar.key,
        )

        assert bucket_file["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert bucket_file["ContentLength"] > 0

        res = client.delete(f"/api/users/{user_model.uuid}/avatar", headers=headers)

        assert res.status_code == 204


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

    assert db_user.password_hash != data.old_password
    assert not db_user.is_verified

    db_user.is_verified = True

    db.commit()
    db.refresh(db_user)

    assert db_user.is_verified

    form_data = {"username": user.email, "password": data.new_password}

    response = client.post("/api/auth/login", data=form_data)
    assert response.status_code == 200


# for admin only
def test_get_subscription_history(
    client: TestClient,
    db: Session,
    admin_headers: dict[str, str],
    test_data: s.TestData,
):
    response = client.get(
        f"/api/users/{test_data.test_users[0].uuid}/subscriptions",
        headers=admin_headers,
    )
    assert response.status_code == 200
