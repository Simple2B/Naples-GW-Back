from datetime import datetime, timedelta, UTC
from typing import Sequence
from mypy_boto3_s3 import S3Client
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from pydantic_extra_types.color import Color

from naples import schemas as s, models as m
from naples.config import config
from services.store.add_dns_record import get_subdomain_from_url


CFG = config("testing")


def test_get_store(client: TestClient, headers: dict[str, str], test_data: s.TestData, full_db: Session):
    store_model = full_db.scalar(sa.select(m.Store))
    assert store_model
    response = client.get(f"/api/stores/{store_model.url}", headers=headers)
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
        url="test_url",
        email="user@email.com",
        instagram_url="instagram_url",
        messenger_url="messenger_url",
        title_value="Title",
        title_color="#000000",
        title_font_size=24,
        sub_title_value="Sub Title",
        sub_title_color="#000000",
        sub_title_font_size=18,
    )
    response = client.post("/api/stores/", headers=headers, json=test_store.model_dump())
    assert response.status_code == 201
    store_data = s.StoreOut.model_validate(response.json())

    assert store_data.title.value == test_store.title_value
    assert store_data.sub_title.color == test_store.sub_title_color


def test_upload_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        store_res = client.get(f"/api/stores/{store_model.url}")
        assert store_res.status_code == 200

        store = s.StoreOut.model_validate(store_res.json())
        assert store.main_media and store.main_media.url == store_model.main_media.url

        full_db.refresh(store_model)

        bucket_file = s3_client.get_object(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            Key=store_model.main_media.key,
        )

        assert bucket_file["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert bucket_file["ContentLength"] > 0


def test_update_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "test.jpg"

        update_response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test_2.jpg", f, "image/jpeg")},
        )

        assert update_response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "test_2.jpg"


def test_delete_image(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        delete_res = client.delete("/api/stores/main_media", headers=headers)

        assert delete_res.status_code == 204

        full_db.refresh(store_model)

        assert not store_model.main_media


def test_create_store_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/test_video.mp4", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "test.mp4"


def test_update_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/test_video.mp4", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "test.mp4"

        update_response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test_2.mp4", f, "video/mp4")},
        )

        assert update_response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "test_2.mp4"


def test_delete_video(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/test_video.mp4", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("test.mp4", f, "video/mp4")},
        )
        assert response.status_code == 201

        delete_res = client.delete("/api/stores/main_media", headers=headers)

        assert delete_res.status_code == 204

        full_db.refresh(store_model)

        assert not store_model.main_media


def test_create_store_logo(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/airbnb.svg", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/logo",
            headers=headers,
            files={"logo": ("test.svg", f, "image/svg+xml")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.logo.original_name == "test.svg"


def test_update_store_logo(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/airbnb.svg", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/logo",
            headers=headers,
            files={"logo": ("test.svg", f, "image/svg+xml")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.logo.original_name == "test.svg"

        update_response = client.post(
            "/api/stores/logo",
            headers=headers,
            files={"logo": ("test_2.svg", f, "image/svg+xml")},
        )

        assert update_response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.logo.original_name == "test_2.svg"


def test_delete_store_logo(client: TestClient, headers: dict[str, str], full_db: Session, s3_client: S3Client):
    with open("tests/airbnb.svg", "rb") as f:
        store_model = full_db.scalar(sa.select(m.Store))
        assert store_model

        response = client.post(
            "/api/stores/logo",
            headers=headers,
            files={"logo": ("test.svg", f, "image/svg+xml")},
        )
        assert response.status_code == 201

        delete_res = client.delete("/api/stores/logo", headers=headers)

        assert delete_res.status_code == 204

        full_db.refresh(store_model)

        assert not store_model.logo


def test_update_store(client: TestClient, headers: dict[str, str], full_db: Session):
    store_model = full_db.scalar(sa.select(m.Store))
    assert store_model

    update_data = s.StoreUpdateIn(
        title_value="New Title",
        sub_title_value="New Sub Title",
        title_color=Color("#ffffff"),
        title_font_size=24,
        sub_title_color=Color("#000000"),
        sub_title_font_size=12,
        about_us_description="This is a description",
        messenger_url="",
        url=f"{store_model.uuid}.propertyroster.com",
    )

    response = client.patch("/api/stores/", headers=headers, content=update_data.model_dump_json())
    assert response.status_code == 200

    store = s.StoreOut.model_validate(response.json())

    assert update_data.title_color
    assert update_data.sub_title_color

    assert store.title.value == update_data.title_value
    assert store.sub_title.value == update_data.sub_title_value
    assert store.title.color == update_data.title_color.as_hex()
    assert store.title.font_size == update_data.title_font_size
    assert store.sub_title.color == update_data.sub_title_color.as_hex()
    assert store.sub_title.font_size == update_data.sub_title_font_size
    assert store.about_us
    assert store.about_us.about_us_description == update_data.about_us_description

    more_update_data = s.StoreUpdateIn(
        messenger_url="https://messenger.com",
        phone="1234567890",
        instagram_url="https://instagram.com",
        url="new_url.com",
    )

    response = client.patch("/api/stores/", headers=headers, content=more_update_data.model_dump_json())
    assert response.status_code == 200

    store = s.StoreOut.model_validate(response.json())

    assert store.messenger_url == str(more_update_data.messenger_url)
    assert store.phone == more_update_data.phone
    assert store.instagram_url == str(more_update_data.instagram_url)
    assert store.url == more_update_data.url


def test_get_stores_urls(
    client: TestClient,
    full_db: Session,
):
    store_models = full_db.scalars(sa.select(m.Store)).all()
    assert store_models

    response = client.get("/api/stores/urls")
    assert response.status_code == 200

    stores = s.TraefikData.model_validate(response.json())

    data_stores = [
        s.TraefikStoreData(
            uuid=store.uuid,
            subdomain=get_subdomain_from_url(store.url) or store.uuid,
            store_url=store.url,
        )
        for store in store_models
        if store.url
    ]

    for store in data_stores:
        assert store.subdomain in stores.http.routers
        assert stores.http.routers[store.subdomain].rule == f"Host(`{store.store_url}`)"
        assert stores.http.services[store.subdomain].loadBalancer.servers[0].url == f"http://{CFG.WEB_SERVICE_NAME}"


def test_upload_store_about_us_media(
    client: TestClient,
    headers: dict[str, str],
    full_db: Session,
    s3_client: S3Client,
):
    store_model = full_db.scalar(sa.select(m.Store))
    assert store_model

    with open("tests/house_example.png", "rb") as f:
        response = client.post(
            "/api/stores/about_us/main_media",
            headers=headers,
            files={"about_us_main_media": ("test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        store_res = client.get(f"/api/stores/{store_model.url}")
        assert store_res.status_code == 200

        store = s.StoreOut.model_validate(store_res.json())
        assert store.about_us
        assert store.about_us.about_us_main_media
        assert store.about_us.about_us_main_media.url == store_model.about_us_main_media.url

        full_db.refresh(store_model)

        bucket_file = s3_client.get_object(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            Key=store_model.about_us_main_media.key,
        )

        assert bucket_file["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert bucket_file["ContentLength"] > 0

    db_store = full_db.scalar(sa.select(m.Store))
    assert db_store
    assert db_store.about_us_main_media.original_name == "test.jpg"

    with open("tests/house_example.png", "rb") as f:
        response = client.post(
            "/api/stores/main_media",
            headers=headers,
            files={"main_media": ("main_media_test.jpg", f, "image/jpeg")},
        )
        assert response.status_code == 201

        full_db.refresh(store_model)

        assert store_model.main_media.original_name == "main_media_test.jpg"

    # delete the image
    delete_res = client.delete("/api/stores/about_us/main_media", headers=headers)

    assert delete_res.status_code == 204
    assert not db_store.about_us_main_media
    assert not store_model.about_us_main_media
    assert store_model.main_media.original_name == "main_media_test.jpg"


def test_get_stores_for_admin(
    client: TestClient,
    full_db: Session,
    admin_headers: dict[str, str],
):
    db_stores: Sequence[m.Store] = full_db.scalars(sa.select(m.Store)).all()
    search = db_stores[0].user.email

    response = client.get(
        "/api/stores",
        headers=admin_headers,
        params={"search": search},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

    # add subscription for users

    full_db.add(
        m.Subscription(
            user_id=db_stores[0].user.id,
            type=s.SubscriptionStatus.ACTIVE.value,
            status=s.SubscriptionStatus.ACTIVE.value,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    full_db.add(
        m.Subscription(
            user_id=db_stores[0].user.id,
            type=s.SubscriptionStatus.INCOMPLETE.value,
            status=s.SubscriptionStatus.INCOMPLETE.value,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    full_db.add(
        m.Subscription(
            user_id=db_stores[1].user.id,
            type=s.SubscriptionStatus.TRIALING.value,
            status=s.SubscriptionStatus.TRIALING.value,
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
        )
    )
    full_db.commit()

    response = client.get(
        "/api/stores", headers=admin_headers, params={"subscription_status": s.SubscriptionFilteringStatus.ACTIVE.value}
    )
    assert response.status_code == 200
    stores = response.json()["items"]
    assert len(stores) == 1

    response = client.get(
        "/api/stores",
        headers=admin_headers,
        params={"subscription_status": s.SubscriptionFilteringStatus.INACTIVE.value},
    )
    assert response.status_code == 200
    stores = response.json()["items"]
    assert stores
    assert len(stores) == 2

    response = client.get("/api/stores/report/download", headers=admin_headers)

    assert response.status_code == 200
    assert response.headers["Content-Disposition"]
