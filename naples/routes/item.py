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


@item_router.get(
    "/{city}/{category}/{type}/{price_min}/{price_max}",
    status_code=status.HTTP_200_OK,
    response_model=s.Items,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_items(
    city_uuid: str | None = None,
    category: s.ItemCategories | None = None,
    type: s.ItemTypes | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.user_id == current_user.id))

    if not store:
        log(log.ERROR, "User [%s] has no store", current_user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no store")

    stmt = sa.select(m.Item).where(
        sa.and_(
            m.Item.is_deleted.is_(False),
            m.Item.store_id == store.id,
        )
    )

    city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == city_uuid))

    if city:
        stmt = stmt.where(m.Item.city_id == city.id)

    if category:
        stmt = stmt.where(m.Item.category == category)

    if type:
        stmt = stmt.where(m.Item.type == type)

    if price_min and price_max:
        stmt = stmt.where(sa.and_(m.Item.price >= price_min, m.Item.price <= price_max))

    items: Sequence[m.Item] = db.scalars(stmt).all()

    return s.Items(items=[cast(s.ItemOut, item) for item in items])


@item_router.get(
    "/filters",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemsFilterData,
)
def get_filters_data(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get data for filter items"""
    # TODO: Implement this
    return s.ItemsFilterData(
        categories=list(s.ItemCategories),
        types=list(s.ItemTypes),
        price_max=0,
        price_min=0,
    )


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

    city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == item_rieltor.item.city_uuid))

    if not city:
        log(log.ERROR, "City [%s] not found", item_rieltor.item.city_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    if item_rieltor.rieltor:
        new_member: m.Member = m.Member(
            **item_rieltor.rieltor.model_dump(),
            store_id=store.id,
            city_id=city.id,
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
