from fastapi.testclient import TestClient

from naples import schemas as s
from naples import models as m
from naples.config import config

from .test_data import TestData

CFG = config("testing")


def test_get_store(client: TestClient, headers: dict[str, str], test_data: TestData):
    store_uuid = test_data.test_stores[0].uuid
    response = client.get(f"/api/stores/{store_uuid}", headers=headers)
    assert response.status_code == 200
    store = s.StoreOut.model_validate(response.json())
    assert store.uuid == test_data.test_stores[0].uuid


def test_create_stote(client: TestClient, headers: dict[str, str], test_data: TestData):
    pass
    # test_store =
    # response = client.post("/api/", headers=headers, job=test_store)
    # assert response.status_code == 200
