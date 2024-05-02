import sqlalchemy as sa

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from naples.database import get_db
from naples.dependency import get_current_user_store
from naples.dependency.store import get_current_store
from naples.logger import log
from naples import schemas as s, models as m


fee_router = APIRouter(prefix="/fee", tags=["Fee"])


@fee_router.get("/{item_uuid}", response_model=s.FeeListOut)
async def get_fees_for_item(item_uuid: str, current_store: m.Store = Depends(get_current_store)):
    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return s.FeeListOut(items=[s.FeeOut.model_validate(fee) for fee in item.fees])


@fee_router.post("/", response_model=s.FeeOut, status_code=201)
async def create_fee(
    data: s.FeeIn, user_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Creating fee {%s} for store {%s}", data, user_store)

    item = user_store.get_item_by_uuid(data.item_uuid)

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    new_fee = m.Fee(
        name=data.name,
        amount=data.amount,
        item_id=item.id,
        visible=data.visible,
    )
    db.add(new_fee)
    db.commit()

    log(log.INFO, f"Created fee {new_fee} for item {item}")

    return s.FeeOut.model_validate(new_fee)


@fee_router.put("/{fee_uuid}", response_model=s.FeeOut)
async def update_fee(
    fee_uuid: str, data: s.FeeIn, user_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, f"Updating fee {fee_uuid} with data {data} for store {user_store}")

    item = user_store.get_item_by_uuid(data.item_uuid)
    if not item:
        log(log.ERROR, "Item not found for store {%s}", user_store)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    fee = item.get_fee_by_uuid(fee_uuid)
    if not fee:
        log(log.ERROR, "Fee not found for item {%s}", item)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")

    fee.name = data.name
    fee.amount = data.amount
    fee.visible = data.visible
    db.commit()

    log(log.INFO, f"Updated fee {fee} for item {item}")

    return s.FeeOut.model_validate(fee)


@fee_router.delete("/{fee_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee(
    fee_uuid: str, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, f"Deleting fee {fee_uuid} for user {current_store}")

    fee = db.scalar(sa.select(m.Fee).filter(m.Fee.uuid == fee_uuid))

    if not fee:
        log(log.ERROR, f"Fee not found for uuid {fee_uuid}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")

    if fee.item.store_id != current_store.id:
        log(log.ERROR, f"User {current_store} does not own fee {fee}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own this fee")

    fee.is_deleted = True
    db.commit()

    log(log.INFO, f"Deleted fee {fee}")
