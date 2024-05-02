from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_create_fee(client: TestClient, full_db: Session, headers: dict[str, str]):
    test_item = full_db.scalar(select(m.Item))
    assert test_item

    req_payload = s.FeeIn(name="Test Fee", amount=100.0, item_uuid=test_item.uuid, visible=True)

    res = client.post("/api/fee/", json=req_payload.model_dump(), headers=headers)
    assert res.status_code == 201
    fee = s.FeeOut.model_validate(res.json())

    fee_model = full_db.scalar(select(m.Fee))
    assert fee_model
    assert fee.name == fee_model.name


def test_get_fees_for_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    test_item = full_db.scalar(select(m.Item))
    assert test_item

    fee_one = m.Fee(name="Fee One", amount=100.0, item_id=test_item.id, visible=True)
    fee_two = m.Fee(name="Fee Two", amount=200.0, item_id=test_item.id, visible=True)
    full_db.add_all([fee_one, fee_two])
    full_db.commit()

    res = client.get(f"/api/fee/{test_item.uuid}", headers=headers, params={"store_url": test_item.store.url})
    assert res.status_code == 200
    fees = s.FeeListOut.model_validate(res.json())
    assert len(fees.items) == 2
    assert fees.items[0].name == fee_one.name
    assert fees.items[1].name == fee_two.name


def test_update_fee(client: TestClient, full_db: Session, headers: dict[str, str]):
    test_item = full_db.scalar(select(m.Item))
    assert test_item

    fee = m.Fee(name="Fee One", amount=100.0, item_id=test_item.id, visible=True)

    full_db.add(fee)
    full_db.commit()

    req_payload = s.FeeIn(name="Updated Fee", amount=200.0, visible=False, item_uuid=test_item.uuid)
    res = client.put(
        f"/api/fee/{fee.uuid}",
        json=req_payload.model_dump(),
        headers=headers,
    )
    assert res.status_code == 200
    updated_fee = s.FeeOut.model_validate(res.json())

    fee_model = full_db.get(m.Fee, fee.id)
    assert fee_model

    assert updated_fee.name == fee_model.name
    assert updated_fee.amount == fee_model.amount
    assert updated_fee.visible == fee_model.visible


def test_delete_fee(client: TestClient, full_db: Session, headers: dict[str, str]):
    test_item = full_db.scalar(select(m.Item))
    assert test_item

    fee = m.Fee(name="Fee One", amount=100.0, item_id=test_item.id, visible=True)

    full_db.add(fee)
    full_db.commit()

    res = client.delete(
        f"/api/fee/{fee.uuid}",
        headers=headers,
    )

    assert res.status_code == 204
    deleted_fee = full_db.get(m.Fee, fee.id)
    assert deleted_fee and deleted_fee.is_deleted

    fees_res = client.get(f"/api/fee/{test_item.uuid}", headers=headers, params={"store_url": test_item.store.url})
    assert fees_res.status_code == 200
    fees = s.FeeListOut.model_validate(fees_res.json())
    assert len(fees.items) == 0
