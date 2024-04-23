from typing import Generator
import uuid

import pytest
from dotenv import load_dotenv

load_dotenv("tests/test.env")

# ruff: noqa: F401 E402
from fastapi.testclient import TestClient
from sqlalchemy import orm

from naples.main import api
from naples import models as m
from naples import schemas as s

from .test_data import TestData


@pytest.fixture
def db(test_data: TestData) -> Generator[orm.Session, None, None]:
    from naples.database import db, get_db

    with db.Session() as session:
        db.Model.metadata.drop_all(bind=session.bind)
        db.Model.metadata.create_all(bind=session.bind)
        for test_user in test_data.test_users:
            user = m.User(
                id=test_user.id,
                email=test_user.email,
                password=test_user.password,
            )
            session.add(user)

        for test_store in test_data.test_stores:
            store = m.Store(
                uuid=test_store.uuid,
                name=test_store.name,
                header=test_store.header,
                sub_header=test_store.sub_header,
                url=test_store.url,
                logo_url=test_store.logo_url,
                about_us=test_store.about_us,
                email=test_store.email,
                instagram_url=test_store.instagram_url,
                messenger_url=test_store.messenger_url,
                user_id=test_store.user_id,
            )
            session.add(store)

        session.commit()

        def override_get_db() -> Generator:
            yield session

        api.dependency_overrides[get_db] = override_get_db
        yield session
        # clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def client(db) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""
    with TestClient(api) as c:
        yield c


@pytest.fixture
def test_data() -> Generator[TestData, None, None]:
    """Returns a TestData object"""
    with open("tests/test_data.json", "r") as f:
        yield TestData.model_validate_json(f.read())


@pytest.fixture
def headers(
    client: TestClient,
    test_data: TestData,
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
