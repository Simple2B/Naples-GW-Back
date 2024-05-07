from datetime import datetime, UTC

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_created_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    item = full_db.scalar(select(m.Item))
    assert item

    date = datetime.now()

    req_payload = s.BookedDatesBatchIn(item_uuid=item.uuid, dates=[date])

    res = client.post("/api/booked_dates", content=req_payload.model_dump_json(), headers=headers)

    assert res.status_code == 201

    item_res = client.get(f"/api/items/{item.uuid}", params={"store_url": store.url})

    assert item_res.status_code == 200

    item_data = s.ItemDetailsOut.model_validate(item_res.json())

    assert item_data.booked_dates

    assert item_data.booked_dates[0] == date


def test_get_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    booked_date_one = m.BookedDate(date=datetime.now(), item_id=item.id)
    booked_date_two = m.BookedDate(date=datetime.now(), item_id=item.id)
    full_db.add([booked_date_one, booked_date_two])
    full_db.commit()

    res = client.get(f"/api/booked_dates/{item.uuid}", headers=headers)
    assert res.status_code == 200

    booked_dates = s.BookedDateListOut.model_validate(res.json())
    assert len(booked_dates.items) == 2

    assert booked_dates.items[0].date == booked_date_one.date


def test_delete_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    pass
