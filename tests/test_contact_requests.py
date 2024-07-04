from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_create_contact_request(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    req_payload = s.ContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="john_doe@buu.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
    )

    res = client.post(
        f"/api/contact_requests?store_url={store.url}", content=req_payload.model_dump_json(), headers=headers
    )
    assert res.status_code == 201
    contact_request = s.ContactRequestOut.model_validate(res.json())

    contact_request_model = full_db.scalar(select(m.ContactRequest))
    assert contact_request_model

    assert contact_request.first_name == contact_request_model.first_name
    assert contact_request.last_name == contact_request_model.last_name
    assert contact_request.email == contact_request_model.email


def test_create_contact_request_for_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    item = store.items[0]
    assert item

    req_payload = s.ContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="john_doe@buu.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
        item_uuid=item.uuid,
    )

    res = client.post(
        f"/api/contact_requests?store_url={store.url}", content=req_payload.model_dump_json(), headers=headers
    )
    assert res.status_code == 201
    contact_request = s.ContactRequestOut.model_validate(res.json())

    assert contact_request.item_uuid == item.uuid


def test_get_contact_requests(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    item = store.items[0]
    assert item

    request_one = m.ContactRequest(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
        store_id=store.id,
    )
    request_two = m.ContactRequest(
        first_name="Jane",
        last_name="Doe",
        email="def@def.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
        store_id=store.id,
        item_id=item.id,
    )
    full_db.add_all([request_one, request_two])
    full_db.commit()
    full_db.refresh(store)

    res = client.get("/api/contact_requests/", headers=headers)
    assert res.status_code == 200
    contact_requests = s.ContactRequestListOut.model_validate(res.json())

    assert len(contact_requests.items) == len(store.contact_requests)

    assert contact_requests.items[0].first_name == request_two.first_name
    assert contact_requests.items[1].item_uuid == request_one.item_uuid

    just_jane = client.get("/api/contact_requests", headers=headers, params={"search": "Jane"})
    assert just_jane.status_code == 200
    jane = s.ContactRequestListOut.model_validate(just_jane.json())
    assert len(jane.items) == 1
    assert jane.items[0].first_name == "Jane"

    john_model = full_db.scalar(select(m.ContactRequest).where(m.ContactRequest.first_name == "John"))
    assert john_model

    john_model.status = s.ContactRequestStatus.PROCESSED.value
    full_db.commit()

    processed = client.get(
        "/api/contact_requests", headers=headers, params={"status": s.ContactRequestStatus.PROCESSED.value}
    )
    assert processed.status_code == 200
    processed_requests = s.ContactRequestListOut.model_validate(processed.json())

    assert len(processed_requests.items) == 1
    assert processed_requests.items[0].first_name == "John"


def test_update_contact_request_status(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    payload = s.ContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
    )

    res = client.post(
        f"/api/contact_requests?store_url={store.url}", content=payload.model_dump_json(), headers=headers
    )

    assert res.status_code == 201

    contact_request = s.ContactRequestOut.model_validate(res.json())
    assert contact_request.status == s.ContactRequestStatus.CREATED

    res = client.put(
        f"/api/contact_requests/{contact_request.uuid}",
        content=s.ContactRequestUpdateIn(status=s.ContactRequestStatus.PROCESSED).model_dump_json(),
        headers=headers,
    )

    assert res.status_code == 200
    updated_contact_request = s.ContactRequestOut.model_validate(res.json())
    assert updated_contact_request.status == s.ContactRequestStatus.PROCESSED


def test_delete_contact_request(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    contact_request = m.ContactRequest(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this item",
        check_in=datetime.now(),
        check_out=datetime.now(),
        store_id=store.id,
    )
    full_db.add(contact_request)
    full_db.commit()
    full_db.refresh(store)

    res = client.delete(f"/api/contact_requests/{contact_request.uuid}", headers=headers)
    assert res.status_code == 204

    full_db.refresh(contact_request)

    assert contact_request.is_deleted

    res = client.get("/api/contact_requests", headers=headers)
    assert res.status_code == 200
    contact_requests = s.ContactRequestListOut.model_validate(res.json())
    assert len(contact_requests.items) == 0
