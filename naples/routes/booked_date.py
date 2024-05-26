import sqlalchemy as sa
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, status, HTTPException

from naples.logger import log
from naples import schemas as s, models as m
from naples.database import get_db
from naples.dependency import get_current_user_store


booked_date_router = APIRouter(prefix="/booked_dates", tags=["booked_dates"])


@booked_date_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booked_dates(
    data: s.BookedDatesBatchIn,
    store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Creating booked dates for item {%s}", data.item_uuid)

    item = store.get_item_by_uuid(data.item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    booked_date = m.BookedDate(
        from_date=data.from_date,
        to_date=data.to_date,
        item_id=item.id,
    )
    db.add(booked_date)
    db.commit()

    log(log.INFO, "Created booked dates for item {%s}", data.item_uuid)


@booked_date_router.get("/{item_uuid}", status_code=status.HTTP_200_OK, response_model=s.BookedDateListOut)
async def get_booked_dates_for_item(item_uuid: str, store: m.Store = Depends(get_current_user_store)):
    log(log.INFO, "Getting booked dates for item {%s}", item_uuid)
    item = store.get_item_by_uuid(item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return s.BookedDateListOut(
        items=[
            s.BookedDateOut(
                uuid=booked_date.uuid,
                from_date=booked_date.from_date,
                to_date=booked_date.to_date,
            )
            for booked_date in item._booked_dates
            if not booked_date.is_deleted
        ]
    )


@booked_date_router.put("/delete", status_code=status.HTTP_204_NO_CONTENT, description="Delete a batch of booked dates")
async def delete_booked_dates(
    data: s.BookedDateDeleteBatchIn, store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    """
    Delete a batch of booked dates for an item
    """
    log(log.INFO, "Deleting booked dates for item {%s}", data.item_uuid)

    item = store.get_item_by_uuid(data.item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    for date_uuid in data.dates_uuids:
        booked_date = db.scalar(sa.select(m.BookedDate).where(m.BookedDate.uuid == date_uuid))
        if not booked_date:
            log(log.WARNING, "Booked date with UUID {%s} not found", date_uuid)
            continue
        booked_date.is_deleted = True
    db.commit()

    log(log.INFO, "Deleted booked dates for item {%s}", data.item_uuid)
