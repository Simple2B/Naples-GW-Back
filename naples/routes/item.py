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


@item_router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.Items,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_items(
    data: s.ItemsFilterDataIn,
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

    city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == data.city_uuid))

    if city:
        stmt = stmt.where(m.Item.city_id == city.id)

    if data.category:
        stmt = stmt.where(m.Item.category == data.category)

    if data.type:
        stmt = stmt.where(m.Item.type == data.type)

    if data.price_min and data.price_max:
        stmt = stmt.where(sa.and_(m.Item.price >= data.price_min, m.Item.price <= data.price_max))

    items: Sequence[m.Item] = db.scalars(stmt).all()

    return s.Items(items=[cast(s.ItemOut, item) for item in items])


@item_router.get(
    "/filters",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemsFilterDataOut,
)
def get_filters_data(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get data for filter items"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.user_id == current_user.id))

    if not store:
        log(log.ERROR, "User [%s] has no store", current_user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no store")

    items: Sequence[m.Item] = db.scalars(sa.select(m.Item).where(m.Item.store_id == store.id)).all()

    price_min: int = min(item.price for item in items)
    price_max: int = max(item.price for item in items)

    return s.ItemsFilterDataOut(
        categories=list(s.ItemCategories),
        types=list(s.ItemTypes),
        price_max=price_max,
        price_min=price_min,
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
    data: s.ItemRieltorIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a new item"""
    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.user_id == current_user.id))

    if not store:
        log(log.ERROR, "User [%s] has no store", current_user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no store")

    if data.rieltor:
        new_member: m.Member = m.Member(
            **data.rieltor.model_dump(),
            store_id=store.id,
        )
        db.add(new_member)
        db.flush()

    city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == data.item.city_uuid))

    if not city:
        log(log.ERROR, "City [%s] not found", data.item.city_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    new_item: m.Item = m.Item(
        name=data.item.name,
        description=data.item.description,
        latitude=data.item.latitude,
        longitude=data.item.longitude,
        address=data.item.address,
        size=data.item.size,
        bedrooms_count=data.item.bedrooms_count,
        bathrooms_count=data.item.bathrooms_count,
        stage=data.item.stage,
        category=data.item.category,
        type=data.item.type,
        store_id=store.id,
        realtor_id=new_member.id,
        city_id=city.id,
    )

    db.add(new_item)
    db.commit()

    log(log.INFO, "Created item [%s] for store [%s]", new_item.name, new_item.store_id)
    return new_item
