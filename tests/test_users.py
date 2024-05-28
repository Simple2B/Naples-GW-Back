from fastapi.testclient import TestClient

from naples import schemas as s
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

    user_update = s.UserUpdate(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        phone=phone,
    )

    response = client.patch(
        "/api/users/",
        headers=headers,
        json=user_update.model_dump(),
    )

    assert response.status_code == 200
    users_out = s.Users.model_validate(response.json())
    assert users_out
    assert users_out[0].phone == phone
