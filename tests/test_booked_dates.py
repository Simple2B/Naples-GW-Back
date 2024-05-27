from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_created_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    item = full_db.scalar(select(m.Item))
    assert item

    from_date = datetime.now()
    to_date = datetime.now() + timedelta(days=1)

    req_payload = s.BookedDatesBatchIn(item_uuid=item.uuid, from_date=from_date, to_date=to_date)

    res = client.post("/api/booked_dates", content=req_payload.model_dump_json(), headers=headers)

    assert res.status_code == 201

    item_res = client.get(f"/api/items/{item.uuid}", params={"store_url": store.url})

    assert item_res.status_code == 200

    item_data = s.ItemDetailsOut.model_validate(item_res.json())
    assert item_data.booked_dates
    assert item_data.booked_dates[0].from_date == from_date
    assert item_data.booked_dates[0].to_date == to_date


def test_get_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    booked_date_one = m.BookedDate(from_date=datetime.now(), to_date=datetime.now() + timedelta(3), item_id=item.id)
    booked_date_two = m.BookedDate(
        from_date=datetime.now() + timedelta(4), to_date=datetime.now() + timedelta(7), item_id=item.id
    )

    full_db.add_all([booked_date_one, booked_date_two])
    full_db.commit()

    res = client.get(f"/api/booked_dates/{item.uuid}", headers=headers)
    assert res.status_code == 200

    booked_dates = s.BookedDateListOut.model_validate(res.json())
    assert len(booked_dates.items) == 2

    assert booked_dates.items[0].from_date == booked_date_one.from_date
    assert booked_dates.items[1].from_date == booked_date_two.from_date


def test_delete_booked_dates(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    booked_date_one = m.BookedDate(from_date=datetime.now(), to_date=datetime.now() + timedelta(3), item_id=item.id)
    booked_date_two = m.BookedDate(
        from_date=datetime.now() + timedelta(4), to_date=datetime.now() + timedelta(7), item_id=item.id
    )

    full_db.add_all([booked_date_one, booked_date_two])
    full_db.commit()
    full_db.refresh(item)

    req_payload = s.BookedDateDeleteBatchIn(item_uuid=item.uuid, dates_uuids=[booked_date_one.uuid])

    res = client.put("/api/booked_dates/delete", content=req_payload.model_dump_json(), headers=headers)

    assert res.status_code == 204

    item_res = client.get(f"/api/items/{item.uuid}", params={"store_url": item.store.url})

    assert item_res.status_code == 200

    item_data = s.ItemDetailsOut.model_validate(item_res.json())

    assert len(item_data.booked_dates) == 1
    assert item_data.booked_dates[0].from_date == booked_date_two.from_date
    assert item_data.booked_dates[0].to_date == booked_date_two.to_date

    dates_list_res = client.get(f"/api/booked_dates/{item.uuid}", headers=headers)

    assert dates_list_res.status_code == 200

    booked_dates = s.BookedDateListOut.model_validate(dates_list_res.json())
    assert len(booked_dates.items) == 1

    assert booked_dates.items[0].from_date == booked_date_two.from_date
    assert booked_dates.items[0].to_date == booked_date_two.to_date
