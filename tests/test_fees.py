from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_create_fee(client: TestClient, full_db: Session, headers: dict[str, str], test_data: s.TestData):
    test_item = full_db.scalar(select(m.Item))
    assert test_item

    req_payload = s.FeeIn(name="Test Fee", amount=100.0, item_uuid=test_item.uuid, visible=True)

    res = client.post("/api/fee/", json=req_payload.model_dump(), headers=headers)
    assert res.status_code == 201
    fee = s.FeeOut.model_validate(res.json())

    fee_model = full_db.scalar(select(m.Fee))
    assert fee_model
    assert fee.name == fee_model.name


def test_get_fees_for_item():
    pass


def test_update_fee():
    pass


def test_delete_fee():
    pass
