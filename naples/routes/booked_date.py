from fastapi import APIRouter, Depends, status, HTTPException

from naples.logger import log
from naples import schemas as s, models as m
from naples.database import get_db
from naples.dependency import get_current_user_store


booked_date_router = APIRouter(prefix="/booked_dates", tags=["booked_dates"])


@booked_date_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booked_dates(
    data: s.BookedDatesBatchIn, store: m.Store = Depends(get_current_user_store), db=Depends(get_db)
):
    log(log.INFO, "Creating booked dates for item {%s}", data.item_uuid)

    item = store.get_item_by_uuid(data.item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    for booked_date in data.dates:
        booked_date = m.BookedDate(date=booked_date, item_id=item.id)
        db.add(booked_date)
    db.commit()

    log(log.INFO, "Created booked dates for item {%s}", data.item_uuid)


@booked_date_router.get("/{item_uuid}", status_code=status.HTTP_200_OK, response_model=s.BookedDateListOut)
async def get_booked_dates_for_item(item_uuid: str):
    pass


@booked_date_router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booked_dates(data: s.BookedDatesBatchIn):
    pass
