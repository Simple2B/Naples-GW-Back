import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from naples import schemas as s, models as m
from naples.config import config


CFG = config("testing")

DUMMY_FILE_BASE_64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/4QA6RXhpZgAATU0AKgAAAAgAA1IBAAABAAEA"


def test_get_store(client: TestClient, headers: dict[str, str], test_data: s.TestData, full_db: Session):
    store_model = full_db.scalar(sa.select(m.Store))
    assert store_model
    store_uuid = store_model.uuid
    response = client.get(f"/api/stores/{store_uuid}", headers=headers)
    assert response.status_code == 200
    store = s.StoreOut.model_validate(response.json())
    assert store.email == store_model.email


def test_create_store(
    client: TestClient,
    headers: dict[str, str],
    db: Session,
):
    user = db.scalar(sa.select(m.User))
    assert user

    test_store = s.StoreIn(
        header="Header",
        sub_header="Sub Header",
        url="test_url",
        logo_url="logo_url",
        email="user@email.com",
        instagram_url="instagram_url",
        messenger_url="messenger_url",
    )
    response = client.post("/api/stores/", headers=headers, json=test_store.model_dump())
    assert response.status_code == 201


def test_upload_image(client: TestClient, headers: dict[str, str], full_db: Session):
    # TODO: TO BE IMPLEMENTED
    # store_model = full_db.scalar(sa.select(m.Store))
    # assert store_model

    # image_payload = s.FileIn(name="test.jpg", file_base64=DUMMY_FILE_BASE_64, type=s.FileType.IMAGE.value)

    # response = client.post(
    #     "/api/stores/image",
    #     headers=headers,
    #     content=image_payload.model_dump_json(),
    # )
    # assert response.status_code == 201
    pass


def test_update_image(client: TestClient, headers: dict[str, str], full_db: Session):
    # TODO: TO BE IMPLEMENTED
    # store_model = full_db.scalar(sa.select(m.Store))
    # assert store_model

    # image_payload = s.FileIn(name="test.jpg", file_base64=DUMMY_FILE_BASE_64, type=s.FileType.IMAGE.value)

    # response = client.put(
    #     f"/api/stores/image/{store_model.uuid}",
    #     headers=headers,
    #     content=image_payload.model_dump_json(),
    # )
    # assert response.status_code == 201
    pass
