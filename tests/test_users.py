from fastapi.testclient import TestClient

from naples import schemas as s
from sqlalchemy.orm import Session
from naples.config import config

from .test_data import TestData

CFG = config("testing")


def test_get_me(client: TestClient, headers: dict[str, str], test_data: TestData):
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    user = s.User.model_validate(response.json())
    assert user.username == test_data.test_users[0].username


def test_get_users(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    test_data: TestData,
):
    response = client.get(
        "/api/users/",
        headers=headers,
    )
    assert response.status_code == 200
    users_out = s.Users.model_validate(response.json())
    assert len(users_out.users) == len(test_data.test_users)
