from typing import Sequence, cast
from fastapi import Depends, APIRouter, status, HTTPException
from fastapi_pagination import Page, Params, paginate
# from fastapi_pagination.ext.sqlalchemy import paginate


import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples.dependency import get_current_user, get_current_store
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
    current_store: m.Store = Depends(get_current_store),
):
    """Get item by UUID"""

    item: m.Item | None = db.scalar(
        sa.select(m.Item).where(m.Item.uuid == item_uuid, m.Item.store_id == current_store.id)
    )

    if not item:
        log(log.ERROR, "Item [%s] not found for store [%s]", item_uuid, current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return item


@item_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.ItemOut],
    responses={
        404: {"description": "Store not found"},
        403: {"description": "Invalid URL"},
        400: {"description": "Store URL is not provided"},
    },
)
def get_items(
    city_uuid: str | None = None,
    category: str | None = None,
    type: str | None = None,
    price_max: int | None = None,
    price_min: int | None = None,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_store),
):
    """Get items by filters and pagination"""

    stmt = sa.select(m.Item).where(
        sa.and_(
            m.Item.is_deleted.is_(False),
            m.Item.store_id == current_store.id,
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

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [cast(s.ItemOut, item) for item in db_items]

    return paginate(items, params)


@item_router.get(
    "/filters/data",
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

    if data.realtor:
        new_member: m.Member = m.Member(
            **data.realtor.model_dump(),
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
        price=data.item.price,
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
