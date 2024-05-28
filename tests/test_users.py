from fastapi.testclient import TestClient
import sqlalchemy as sa

from naples import schemas as s
import naples.models as m
from sqlalchemy.orm import Session
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
