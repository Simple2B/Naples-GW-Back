from typing import Sequence
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from moto import mock_aws

from naples import schemas as s
from naples import models as m

from naples.config import config
from naples.dependency import get_s3_connect


CFG = config("testing")


def test_get_item(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    store: m.Store | None = full_db.scalar(select(m.Store))
    assert store

    store_url: str = store.url
    item_uuid = test_data.test_items[0].uuid
    response = client.get(f"/api/items/{item_uuid}?store_url={store_url}", headers=headers)
    assert response.status_code == 200
    item = s.ItemOut.model_validate(response.json())
    assert item.uuid == test_data.test_items[0].uuid


@mock_aws
def test_create_item(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    city: m.City | None = full_db.scalar(select(m.City))
    assert city
    test_realtor = full_db.scalar(select(m.Member))

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
        category=s.ItemCategories.BUY.value,
        type=s.ItemTypes.HOUSE.value,
        price=1000,
        city_uuid=city.uuid,
        realtor_uuid=test_realtor.uuid,
    )

    # creating a bucket
    s3 = get_s3_connect(CFG)
    s3.create_bucket(Bucket=CFG.AWS_S3_BUCKET_NAME)

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
    category = s.ItemCategories.BUY.value

    response = client.get(f"/api/items?city_uuid={city_uuid}&category={category}&store_url=", headers=headers)
    assert response.status_code == 403

    type = s.ItemTypes.HOUSE.value
    price_min = 0
    price_max = 10000

    response = client.get(
        f"/api/items?type={type}&price_min={price_min}&price_max={price_max}&store_url={store_url}", headers=headers
    )
    assert response.status_code == 200
