from typing import Sequence, cast
from fastapi import Depends, APIRouter, status, HTTPException

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples.dependency import get_current_user
from naples.database import get_db


item_router = APIRouter(prefix="/items", tags=["Items"])


@item_router.get(
    "/{item_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def get_item(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get item by UUID"""

    item: m.Item | None = db.scalar(sa.select(m.Item).where(m.Item.uuid == item_uuid))
    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@item_router.get("/", status_code=status.HTTP_200_OK, response_model=s.Items)
def get_items(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    query = sa.select(m.Item)
    items: Sequence[m.Item] = db.scalars(query).all()
    return s.Items(items=cast(list, items))


@item_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def create_item(
    item_rieltor: s.ItemRieltorIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a new item"""
    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.user_id == current_user.id))

    if not store:
        log(log.ERROR, "User [%s] has no store", current_user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no store")

    if item_rieltor.rieltor:
        new_member: m.Member = m.Member(
            **item_rieltor.rieltor.model_dump(),
            store_id=store.id,
        )
        db.add(new_member)
        db.flush()

    new_item: m.Item = m.Item(
        **item_rieltor.item.model_dump(),
        store_id=store.id,
        realtor_id=new_member.id,
    )

    db.add(new_item)
    db.commit()

    log(log.INFO, "Created item [%s] for store [%s]", new_item.name, new_item.store_id)
    return new_item
