from mypy_boto3_s3 import S3Client
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from naples import schemas as s, models as m
from naples.config import config


CFG = config("testing")


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


def test_upload_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/image",
            headers=headers,
            files={"image": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        store_res = client.get(f"/api/stores/{store_model.uuid}")
        assert store_res.status_code == 200

        store = s.StoreOut.model_validate(store_res.json())
        assert store.image_url

        full_db.refresh(store_model)

        bucket_file = s3_client.get_object(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            Key=store_model.image.key,
        )

        assert bucket_file["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert bucket_file["ContentLength"] > 0


def test_update_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/image",
            headers=headers,
            files={"image": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.image.original_name == "test.jpg"

        update_response = client.post(
            "/api/stores/image",
            headers=headers,
            files={"image": ("test_2.jpg", f, "image/jpeg")},
        )

        assert update_response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.image.original_name == "test_2.jpg"


def test_delete_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/image",
            headers=headers,
            files={"image": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        delete_res = client.delete("/api/stores/image", headers=headers)

        assert delete_res.status_code == 204

        full_db.refresh(store_model)

        assert not store_model.image


def test_create_store_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/video",
            headers=headers,
            files={"video": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.video.original_name == "test.mp4"


def test_update_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/video",
            headers=headers,
            files={"video": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.video.original_name == "test.mp4"

        update_response = client.post(
            "/api/stores/video",
            headers=headers,
            files={"video": ("test_2.mp4", f, "video/mp4")},
        )

        assert update_response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.video.original_name == "test_2.mp4"


def test_delete_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/video",
            headers=headers,
            files={"video": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        delete_res = client.delete("/api/stores/video", headers=headers)

        assert delete_res.status_code == 204

        full_db.refresh(store_model)

        assert not store_model.video
