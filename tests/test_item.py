from fastapi.testclient import TestClient
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
from sqlalchemy import select

from naples import schemas as s
from naples import models as m

from naples.config import config


CFG = config("testing")


def test_get_item(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    test_data: s.TestData,
    s3_client: S3Client,
):
    store: m.Store | None = full_db.scalar(select(m.Store))
    assert store

    store_url: str = store.url
    item_uuid = store.items[0].uuid

    with open("tests/house_example.png", "rb") as image:
        response = client.post(
            f"/api/items/{item_uuid}/image/",
            headers=headers,
            files={"image": ("test_1.png", image, "image/png")},
        )
        assert response.status_code == 201

        response = client.post(
            f"/api/items/{item_uuid}/image/",
            headers=headers,
            files={"image": ("test_2.jpeg", image, "image/jpeg")},
        )
        assert response.status_code == 201

        response = client.post(
            f"/api/items/{item_uuid}/image/",
            headers=headers,
            files={"image": ("test_3.png", image, "image/png")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.images_urls

        urls_images = store.items[0].images_urls

        sorted_urls_images = [urls_images[2], urls_images[1], urls_images[0]]

        item_data = s.ItemUpdateIn(images_urls=sorted_urls_images)

        response = client.patch(
            f"/api/items/{item_uuid}?store_url={store_url}",
            headers=headers,
            json=item_data.model_dump(),
        )

        response = client.get(
            f"/api/items/{item_uuid}?store_url={store_url}",
            headers=headers,
            params={
                "store_url": store_url,
                "sorted_urls_images": sorted_urls_images,
            },
        )
        assert response.status_code == 200

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.uuid == store.items[0].uuid
        assert item.images_urls


def test_create_item(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    city: m.City | None = full_db.scalar(select(m.City))
    assert city
    test_realtor = full_db.scalar(select(m.Member))

    assert test_realtor

    test_item = s.ItemIn(
        name="Test Item",
        description="Test Description",
        address="Test Address",
        size=100,
        bedrooms_count=2,
        bathrooms_count=1,
        stage=s.ItemStage.DRAFT.value,
        city_uuid=city.uuid,
        realtor_uuid=test_realtor.uuid,
        adults=5,
    )

    response = client.post(
        "/api/items/",
        json=test_item.model_dump(),
        headers=headers,
    )
    assert response.status_code == 201


def test_get_filters_data(client: TestClient, headers: dict[str, str], full_db: Session):
    store = full_db.scalar(select(m.Store))
    assert store
    response = client.get(
        "/api/items/filters/data",
        params={
            "store_url": store.url,
        },
    )
    assert response.status_code == 200

    filters_data = s.ItemsFilterDataOut.model_validate(response.json())

    assert filters_data.locations
    assert filters_data.adults == 5


def test_get_items(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    store = full_db.scalar(select(m.Store))
    assert store

    item = full_db.scalar(select(m.Item).where(m.Item.stage == s.ItemStage.DRAFT.value))
    assert item

    assert item.id in [i.id for i in store.items]

    store_url = store.url
    size = 2
    response = client.get(
        "/api/items",
        params={
            "store_url": store_url,
            "page": 1,
            "size": size,
        },
    )
    assert response.status_code == 200

    items = s.Items.model_validate(response.json()).items
    assert items
    assert len(items) == size  # We have 5 items in the store, but only 3 are published

    assert item.uuid not in [i.uuid for i in items]

    response = client.get(
        "/api/items",
        params={
            "store_url": store_url,
            "page": 2,
            "size": size,
        },
    )
    assert response.status_code == 200

    res_items = s.Items.model_validate(response.json()).items
    assert res_items

    city: m.City | None = full_db.scalar(select(m.City))
    assert city

    city_uuid = city.uuid

    response = client.get(
        "/api/items",
        headers=headers,
        params={
            "store_url": store.url,
            "page": 1,
            "size": size,
            "city_uuid": city_uuid,
        },
    )
    assert response.status_code == 200

    response = client.get("/api/items", params={"store_url": store.url})
    assert response.status_code == 200

    all_items_response = client.get(
        "/api/items/all",
        params={
            "store_url": store.url,
            "page": 1,
            "size": 100,
        },
    )
    assert all_items_response.status_code == 200

    all_items = s.Items.model_validate(all_items_response.json()).items

    assert len(all_items) == 5


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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.png", image, "image/npg")},
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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemOut.model_validate(response.json())
        assert item.image_url

        update_response = client.post(
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test_2.png", image, "image/npg")},
        )

        assert update_response.status_code == 201

        updated_item = s.ItemOut.model_validate(update_response.json())

        assert updated_item.image_url != item.image_url

        full_db.refresh(item_model)

        assert item_model.main_media.url == updated_item.image_url


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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.png", image, "image/npg")},
        )
        assert response.status_code == 201

        item = s.ItemOut.model_validate(response.json())
        assert item.image_url

        delete_response = client.delete(f"/api/items/{item.uuid}/main_media/", headers=headers)
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.main_media


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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.main_media and item.main_media.url and item.main_media.url


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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.main_media and item.main_media.url

        update_response = client.post(
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test_2.mp4", video, "video/mp4")},
        )

        assert update_response.status_code == 201

        updated_item = s.ItemDetailsOut.model_validate(update_response.json())

        assert updated_item.main_media and updated_item.main_media.url

        assert updated_item.main_media.url != item.main_media.url

        full_db.refresh(item_model)

        assert item_model.main_media.url == updated_item.main_media.url


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
            f"/api/items/{item_model.uuid}/main_media/",
            headers=headers,
            files={"main_media": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.main_media and item.main_media.url

        delete_response = client.delete(f"/api/items/{item.uuid}/main_media/", headers=headers)
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.main_media


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
            data={"title": "Test Document"},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.documents
        assert item.documents[0].title == "Test Document"


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
            data={"title": "Test Document"},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.documents

        delete_response = client.delete(
            f"/api/items/{item.uuid}/document", headers=headers, params={"document_url": item.documents[0].url}
        )
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.documents_urls


def test_add_amenities_to_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    first_amenity = m.Amenity(value="First Amenity")
    second_amenity = m.Amenity(value="Second Amenity")
    full_db.add_all([first_amenity, second_amenity])
    full_db.commit()

    payload = s.ItemAmenitiesIn(amenities_uuids=[first_amenity.uuid, second_amenity.uuid])

    response = client.post(
        f"/api/items/{item_model.uuid}/amenities/",
        headers=headers,
        content=payload.model_dump_json(),
    )
    assert response.status_code == 201

    item = s.ItemDetailsOut.model_validate(response.json())
    assert item.amenities


def test_delete_amenities_from_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    first_amenity = m.Amenity(value="First Amenity")
    second_amenity = m.Amenity(value="Second Amenity")
    full_db.add_all([first_amenity, second_amenity])
    full_db.commit()

    payload = s.ItemAmenitiesIn(amenities_uuids=[first_amenity.uuid, second_amenity.uuid])

    response = client.post(
        f"/api/items/{item_model.uuid}/amenities/",
        headers=headers,
        content=payload.model_dump_json(),
    )
    assert response.status_code == 201

    item = s.ItemDetailsOut.model_validate(response.json())
    assert item.amenities

    response = client.delete(
        f"/api/items/{item_model.uuid}/amenity/{first_amenity.uuid}",
        headers=headers,
    )
    assert response.status_code == 204

    full_db.refresh(item_model)
    assert len(item_model.amenities) == 1


def test_item_list_with_filter(
    client: TestClient,
    full_db: Session,
):
    store = full_db.scalar(select(m.Store))
    assert store

    store_url = store.url
    response = client.get(
        "/api/items",
        params={
            "store_url": store_url,
        },
    )
    assert response.status_code == 200

    items = s.Items.model_validate(response.json()).items
    assert len(items) == 3

    filet_response = client.get(
        "/api/items",
        params={"store_url": store_url, "name": "ITEM3"},
    )
    assert filet_response.status_code == 200

    filtered_items = s.Items.model_validate(filet_response.json()).items
    assert len(filtered_items) == 1
    assert filtered_items[0].name == "test_item3"

    nightly_response = client.get(
        "/api/items",
        params={
            "store_url": store_url,
            "rent_length": [
                s.RentalLength.NIGHTLY.value,
            ],
        },
    )
    assert nightly_response.status_code == 200

    nightly_items = s.Items.model_validate(nightly_response.json()).items

    assert len(nightly_items) == 2


def test_update_item(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
):
    item = full_db.scalar(select(m.Item))
    assert item
    city = full_db.scalars(select(m.City)).all()[1]

    assert city

    update_data = s.ItemUpdateIn(
        name="Updated Item",
        description="Updated Description",
        latitude=0.0,
        longitude=0.0,
        size=100,
        bedrooms_count=2,
        bathrooms_count=1,
        stage=s.ItemStage.DRAFT,
        adults=5,
        show_rates=False,
        show_fees=None,
        show_external_urls=True,
        nightly=None,
        monthly=False,
        annual=True,
    )

    response = client.patch(
        f"/api/items/{item.uuid}",
        headers=headers,
        content=update_data.model_dump_json(),
    )
    assert response.status_code == 200

    updated_item = s.ItemDetailsOut.model_validate(response.json())
    assert updated_item.name == "Updated Item"
    assert updated_item.show_rates is False
    assert updated_item.show_fees is True
    assert updated_item.show_external_urls is True
    assert updated_item.description == "Updated Description"
    assert updated_item.monthly is False
    assert updated_item.annual is True
    assert updated_item.nightly is True

    more_update_data = s.ItemUpdateIn(
        airbnb_url="https://www.airbnb.com/updated",
        vrbo_url="https://www.vrbo.com/updated",
        expedia_url="https://www.expedia.com/updated",
        city_uuid=city.uuid,
    )

    response = client.patch(
        f"/api/items/{item.uuid}",
        headers=headers,
        content=more_update_data.model_dump_json(),
    )
    assert response.status_code == 200

    updated_item = s.ItemDetailsOut.model_validate(response.json())

    if updated_item.show_external_urls and updated_item.external_urls:
        assert updated_item.external_urls.airbnb_url == str(more_update_data.airbnb_url)
        assert updated_item.external_urls.vrbo_url == str(more_update_data.vrbo_url)
        assert updated_item.external_urls.expedia_url == str(more_update_data.expedia_url)
    assert updated_item.city.uuid == city.uuid

    empty_url_string_data = s.ItemUpdateIn(
        airbnb_url="",
    )

    response = client.patch(
        f"/api/items/{item.uuid}",
        headers=headers,
        content=empty_url_string_data.model_dump_json(),
    )
    assert response.status_code == 200

    updated_item = s.ItemDetailsOut.model_validate(response.json())
    assert not updated_item.external_urls.airbnb_url


def test_upload_and_delete_video(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    s3_client: S3Client,
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    with open("tests/house_example.png", "rb") as video:
        response = client.post(
            f"/api/items/{item_model.uuid}/video",
            headers=headers,
            files={"file": ("test.mp4", video, "video/mp4")},
        )
        assert response.status_code == 201

        item = s.ItemDetailsOut.model_validate(response.json())
        assert item.videos_links
        assert len(item.videos_links) == 1

        delete_response = client.delete(
            f"/api/items/{item.uuid}/video", headers=headers, params={"video_url": item.videos_links[0].url}
        )
        assert delete_response.status_code == 204

        full_db.refresh(item_model)
        assert not item_model.videos_links


def test_upload_and_delete_youtube_link(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
):
    item_model = full_db.scalar(select(m.Item))
    assert item_model

    youtube_link = "https://www.youtube.com/watch?v=6JYIGclVQdw"

    data = s.LinkIn(url=youtube_link)

    response = client.post(
        f"/api/items/{item_model.uuid}/link",
        headers=headers,
        json=data.model_dump(),
    )
    assert response.status_code == 201
    assert s.ItemDetailsOut.model_validate(response.json())

    res = client.delete(
        f"/api/items/{item_model.uuid}/link",
        headers=headers,
        params={"link": youtube_link},
    )

    assert res.status_code == 204
    full_db.refresh(item_model)
    assert not item_model.videos_links

    response = client.post(
        f"/api/items/{item_model.uuid}/link",
        headers=headers,
        json=data.model_dump(),
    )
    assert response.status_code == 201
