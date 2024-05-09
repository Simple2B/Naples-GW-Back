from typing import Sequence
from fastapi.testclient import TestClient
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
from sqlalchemy import select

from naples import schemas as s
from naples import models as m

from naples.config import config


CFG = config("testing")


def test_get_item(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    store: m.Store | None = full_db.scalar(select(m.Store))
    assert store

    store_url: str = store.url
    item_uuid = store.items[0].uuid
    response = client.get(f"/api/items/{item_uuid}?store_url={store_url}", headers=headers)
    assert response.status_code == 200
    item = s.ItemOut.model_validate(response.json())
    assert item.uuid == store.items[0].uuid


def test_create_item(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    city: m.City | None = full_db.scalar(select(m.City))
    assert city
    test_realtor = full_db.scalar(select(m.Member))

    assert test_realtor

    test_item = s.ItemIn(
        name="Test Item",
        description="Test Description",
        latitude=0.0,
        longitude=0.0,
        address="Test Address",
        size=100,
        bedrooms_count=2,
        bathrooms_count=1,
        stage=s.ItemStage.DRAFT.value,
        city_uuid=city.uuid,
        realtor_uuid=test_realtor.uuid,
    )

    response = client.post(
        "/api/items/",
        json=test_item.model_dump(),
        headers=headers,
    )
    assert response.status_code == 201


def test_get_filters_data(client: TestClient, headers: dict[str, str], test_data: s.TestData):
    response = client.get("/api/items/filters/data", headers=headers)
    assert response.status_code == 200


def test_get_items(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    store: m.Store | None = full_db.scalar(select(m.Store))
    assert store

    store_url: str = store.url
    size = 4
    response = client.get(f"/api/items?store_url={store_url}&page={1}&size={size}", headers=headers)
    assert response.status_code == 200

    items: Sequence[s.ItemOut] = s.Items.model_validate(response.json()).items
    assert items
    assert len(items) == size

    response = client.get(f"/api/items?store_url={store_url}&page={2}&size={size}", headers=headers)
    assert response.status_code == 200

    res_items: Sequence[s.ItemOut] = s.Items.model_validate(response.json()).items
    assert res_items
    # assert len(res_items) == size

    city: m.City | None = full_db.scalar(select(m.City))
    assert city

    city_uuid = city.uuid

    response = client.get(f"/api/items?city_uuid={city_uuid}&store_url=", headers=headers)
    assert response.status_code == 403

    price_min = 0
    price_max = 10000

    response = client.get(
        f"/api/items?type={type}&price_min={price_min}&price_max={price_max}&store_url={store_url}", headers=headers
    )
    assert response.status_code == 200


def test_delete_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    response = client.delete(f"/api/items/{item.uuid}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/api/items/{item.uuid}", headers=headers, params={"store_url": item.store.url})
    assert response.status_code == 404

    item_model = full_db.scalar(select(m.Item).where(m.Item.uuid == item.uuid))
    assert item_model and item_model.is_deleted


def test_upload_item_main_image(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_image/",
            headers=headers,
            files={"image": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemOut.model_validate(response.json())
        assert item.image_url


def test_update_item_main_image(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_image/",
            headers=headers,
            files={"image": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemOut.model_validate(response.json())
        assert item.image_url

        update_response = client.post(
            f"/api/items/{item_model.uuid}/main_image/",
            headers=headers,
            files={"image": ("test_2.png", image, "image/npg")},
        )

        assert update_response.status_code == 201

        updated_item = s.ItemOut.model_validate(update_response.json())

        assert updated_item.image_url != item.image_url

        full_db.refresh(item_model)

        assert item_model.image_url == updated_item.image_url


def test_delete_main_image(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_image/",
            headers=headers,
            files={"image": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemOut.model_validate(response.json())
        assert item.image_url

        delete_response = client.delete(f"/api/items/{item.uuid}/main_image/", headers=headers)
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.image_url


def test_create_main_item_video(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as video:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_video/",
            headers=headers,
            files={"video": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.video_url


def test_update_main_item_video(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as video:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_video/",
            headers=headers,
            files={"video": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.video_url

        update_response = client.post(
            f"/api/items/{item_model.uuid}/main_video/",
            headers=headers,
            files={"video": ("test_2.mp4", video, "video/mp4")},
        )

        assert update_response.status_code == 201

        updated_item = s.ItemDetailsOut.model_validate(update_response.json())

        assert updated_item.video_url != item.video_url

        full_db.refresh(item_model)

        assert item_model.video_url == updated_item.video_url


def test_delete_main_item_video(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as video:
        response = client.post(
            f"/api/items/{item_model.uuid}/main_video/",
            headers=headers,
            files={"video": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.video_url

        delete_response = client.delete(f"/api/items/{item.uuid}/main_video/", headers=headers)
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.video_url


def test_create_item_image(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_model.uuid}/image/",
            headers=headers,
            files={"image": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.images_urls


def test_delete_item_image(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_model.uuid}/image/",
            headers=headers,
            files={"image": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.images_urls

        delete_response = client.delete(
            f"/api/items/{item.uuid}/image/", headers=headers, params={"image_url": item.images_urls[0]}
        )
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.images_urls


def test_upload_item_document(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as document:
        response = client.post(
            f"/api/items/{item_model.uuid}/document/",
            headers=headers,
            files={"document": ("test.pdf", document, "application/pdf")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.documents_urls


def test_delete_item_document(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as document:
        response = client.post(
            f"/api/items/{item_model.uuid}/document/",
            headers=headers,
            files={"document": ("test.pdf", document, "application/pdf")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.documents_urls

        delete_response = client.delete(
            f"/api/items/{item.uuid}/document", headers=headers, params={"document_url": item.documents_urls[0]}
        )
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.documents_urls
