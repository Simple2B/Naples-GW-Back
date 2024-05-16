from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.testclient import TestClient

from naples import schemas as s, models as m


def test_create_rate(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    req_payload = s.RateIn(
        item_uuid=item.uuid,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=100.0,
        weekend_night=200.0,
        week=300.0,
        month=400.0,
        min_stay=1,
        visible=True,
    )

    res = client.post("/api/rates/", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 201

    rate = s.RateOut.model_validate(res.json())
    rate_model = full_db.scalar(select(m.Rate))
    assert rate_model
    assert rate.night == rate_model.night
    assert rate.weekend_night == rate_model.weekend_night
    assert rate.week == rate_model.week


def test_get_rates_for_item(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    rate = m.Rate(
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=100.0,
        weekend_night=200.0,
        week=300.0,
        month=400.0,
        min_stay=1,
        item_id=item.id,
    )
    invisible_rate = m.Rate(
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=100.0,
        weekend_night=200.0,
        week=300.0,
        month=400.0,
        min_stay=1,
        item_id=item.id,
        visible=False,
    )
    full_db.add_all([rate, invisible_rate])
    full_db.commit()

    res = client.get(f"/api/rates/{item.uuid}", headers=headers)
    assert res.status_code == 200

    rates = s.RateListOut.model_validate(res.json())
    assert rates.items
    assert len(rates.items) == 2
    assert rates.items[0].night == rate.night

    item_details = client.get(f"/api/items/{item.uuid}", params={"store_url": item.store.url}, headers=headers)
    item_res = s.ItemDetailsOut.model_validate(item_details.json())
    assert item_res.rates
    assert len(item_res.rates) == 1


def test_update_rate(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    rate = m.Rate(
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=100.0,
        weekend_night=200.0,
        week=300.0,
        month=400.0,
        min_stay=1,
        item_id=item.id,
    )
    full_db.add(rate)
    full_db.commit()

    req_payload = s.RateIn(
        item_uuid=item.uuid,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=200.0,
        weekend_night=300.0,
        week=400.0,
        month=500.0,
        min_stay=2,
        visible=True,
    )

    res = client.put(f"/api/rates/{rate.uuid}", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 200

    updated_rate = s.RateOut.model_validate(res.json())
    rate_model = full_db.scalar(select(m.Rate))
    assert rate_model
    assert updated_rate.night == rate_model.night


def test_delete_rate(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item

    rate = m.Rate(
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC),
        night=100.0,
        weekend_night=200.0,
        week=300.0,
        month=400.0,
        min_stay=1,
        item_id=item.id,
    )
    full_db.add(rate)
    full_db.commit()

    res = client.delete(f"/api/rates/{rate.uuid}", headers=headers)

    assert res.status_code == 204

    rate_model = full_db.scalar(select(m.Rate).where(m.Rate.uuid == rate.uuid))
    assert rate_model and rate_model.is_deleted

    rates_res = client.get(f"/api/rates/{item.uuid}", headers=headers)
    rates = s.RateListOut.model_validate(rates_res.json())
    assert not rates.items
