from typing import Sequence
from fastapi.testclient import TestClient

from naples import schemas as s

from naples.config import config

from .test_data import TestData

CFG = config("testing")


def test_get_item(client: TestClient, headers: dict[str, str], test_data: TestData):
    item_uuid = test_data.test_items[0].uuid
    response = client.get(f"/api/items/{item_uuid}", headers=headers)
    assert response.status_code == 200
    item = s.ItemOut.model_validate(response.json())
    assert item.uuid == test_data.test_items[0].uuid


def test_create_item(client: TestClient, headers: dict[str, str], test_data: TestData):
    test_rieltor = s.MemberIn(
        name="Test Member",
        email="tets@email.com",
        phone="000000000",
        instagram_url="instagram_url",
        messenger_url="messenger_url",
        avatar_url="avatar_url",
    )
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
    )
    test_item_rieltor = s.ItemRieltorIn(item=test_item, rieltor=test_rieltor)
    response = client.post("/api/items/", headers=headers, json=test_item_rieltor.model_dump())
    assert response.status_code == 201


def test_get_filters_data(client: TestClient, headers: dict[str, str], test_data: TestData):
    response = client.get("/api/items/filters", headers=headers)
    assert response.status_code == 200


def test_get_items(client: TestClient, headers: dict[str, str], test_data: TestData):
    response = client.get("/api/items/", headers=headers)
    assert response.status_code == 200
    items: Sequence[s.ItemOut] = s.Items.model_validate(response.json()).items  # type: ignore
    assert len(items) == len(test_data.test_items)
