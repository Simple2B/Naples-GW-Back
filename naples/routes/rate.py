import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from naples import models as m, schemas as s
from naples.database import get_db
from naples.dependency import get_current_user_store
from naples.logger import log

rates_router = APIRouter(prefix="/rates", tags=["rates"])


@rates_router.get("/{item_uuid}", response_model=s.RateListOut)
async def get_rates_for_item(item_uuid: str, store: m.Store = Depends(get_current_user_store)):
    log(log.INFO, "Getting rates for item {%s} in store {%s}", item_uuid, store)

    item = store.get_item_by_uuid(item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # items = [s.RateOut.model_validate(r) for r in item.rates]
    log(log.INFO, "Found {%s} rates item {%s} in store {%s}", len(item.rates), item_uuid, store)

    return s.RateListOut(items=item.rates)


@rates_router.post("/", response_model=s.RateOut, status_code=status.HTTP_201_CREATED)
async def create_rate(
    data: s.RateIn, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Creating rate in store {%s}", current_store.id)

    item = current_store.get_item_by_uuid(data.item_uuid)

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    new_rate = m.Rate(
        start_date=data.start_date,
        end_date=data.end_date,
        night=data.night,
        weekend_night=data.weekend_night,
        week=data.week,
        month=data.month,
        min_stay=data.min_stay,
        item_id=item.id,
    )
    db.add(new_rate)
    db.commit()

    log(log.INFO, "Created rate {%s} for item {%s}", new_rate.id, item.id)

    return s.RateOut.model_validate(new_rate)


@rates_router.put("/{rate_uuid}", response_model=s.RateOut)
async def update_rate(
    rate_uuid: str,
    rate: s.RateIn,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(
        log.INFO,
        "Updating rate {%s} in store {%s} with payload {%s}",
        rate_uuid,
        current_store.uuid,
        rate.model_dump_json(),
    )

    rate_model = db.scalar(sa.select(m.Rate).where(m.Rate.uuid == rate_uuid))

    if not rate_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found")

    if rate_model.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rate does not belong to store")

    rate_model.start_date = rate.start_date
    rate_model.end_date = rate.end_date
    rate_model.night = rate.night
    rate_model.weekend_night = rate.weekend_night
    rate_model.week = rate.week
    rate_model.month = rate.month
    rate_model.min_stay = rate.min_stay

    db.commit()

    log(log.INFO, "Updated rate {%s} in store {%s}", rate_uuid, current_store.uuid)

    return s.RateOut.model_validate(rate_model)


@rates_router.delete("/{rate_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(
    rate_uuid: str, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Deleting rate uuid {%s} in store {%s}", rate_uuid, current_store.uuid)

    rate = db.scalar(sa.select(m.Rate).where(m.Rate.uuid == rate_uuid))

    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found")

    if rate.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rate does not belong to store")

    rate.is_deleted = True
    db.commit()

    log(log.INFO, "Deleted rate {%s} in store {%s}", rate_uuid, current_store.uuid)
