from fastapi import APIRouter, status, HTTPException

from naples import schemas as s, models as m


booked_date_router = APIRouter(prefix="/booked_dates", tags=["booked_dates"])


@booked_date_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booked_dates(data: s.BookedDatesBatchIn):
    pass


@booked_date_router.get("/{item_uuid}", status_code=status.HTTP_200_OK, response_model=s.BookedDateListOut)
async def get_booked_dates_for_item(item_uuid: str):
    pass


@booked_date_router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booked_dates(data: s.BookedDatesBatchIn):
    pass
