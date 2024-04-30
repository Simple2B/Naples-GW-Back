from fastapi.testclient import TestClient

from naples import schemas as s

from naples.config import config

from naples import schemas as s


CFG = config("testing")


def test_get_store(client: TestClient, headers: dict[str, str], test_data: s.TestData):
    store_uuid = test_data.test_stores[0].uuid
    response = client.get(f"/api/stores/{store_uuid}", headers=headers)
    assert response.status_code == 200
    store = s.StoreOut.model_validate(response.json())
    assert store.uuid == test_data.test_stores[0].uuid


def test_create_stote(client: TestClient, headers: dict[str, str], test_data: s.TestData):
    test_store = s.StoreIn(
        name="Test Store",
        header="Header",
        sub_header="Sub Header",
        url="test_url",
        logo_url="logo_url",
        about_us="about_us",
        email="user@email.com",
        instagram_url="instagram_url",
        messenger_url="messenger_url",
    )
    response = client.post("/api/stores/", headers=headers, json=test_store.model_dump())
    assert response.status_code == 201
