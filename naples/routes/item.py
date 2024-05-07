from typing import Sequence

from fastapi import Depends, APIRouter, status, HTTPException
from fastapi_pagination import Page, Params, paginate

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples.dependency import get_current_user, get_current_store, get_current_user_store
from naples.database import get_db

from naples.config import config

CFG = config()


item_router = APIRouter(prefix="/items", tags=["Items"])


@item_router.get(
    "/{item_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def get_item_by_uuid(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_store),
):
    """Get item by UUID"""

    item: m.Item | None = db.scalar(
        sa.select(m.Item).where(m.Item.uuid == item_uuid, m.Item.store_id == current_store.id)
    )

    if not item or item.is_deleted:
        log(log.ERROR, "Item [%s] not found for store [%s]", item_uuid, current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return s.ItemDetailsOut.model_validate(item)


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

    # TODO: Refactor this filter
    # if price_min and price_max:
    #     stmt = stmt.where(sa.and_(m.Item.min_price >= price_min, m.Item.max_price <= price_max))

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [s.ItemOut.model_validate(item) for item in db_items]

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

    price_min: int = min(int(item.min_price) for item in items)
    price_max: int = max(int(item.max_price) for item in items)

    return s.ItemsFilterDataOut(
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

# ItemDataIn
def create_item(
    new_item: s.ItemIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Create a new item"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.user_id == current_user.id))

    if not store:
        log(log.ERROR, "User [%s] has no store", current_user.email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no store")

    realtor: m.Member | None = db.scalar(sa.select(m.Member).where(m.Member.uuid == new_item.realtor_uuid))

    if not realtor or realtor.store_id != store.id:
        log(log.ERROR, "Realtor [%s] not found", new_item.realtor_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Realtor not found")

    city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == new_item.city_uuid))

    if not city:
        log(log.ERROR, "City [%s] not found", new_item.city_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

    new_item_model: m.Item = m.Item(
        **new_item.model_dump(exclude={"realtor_uuid", "city_uuid"}),
        realtor_id=realtor.id,
        store_id=store.id,
        city_id=city.id,
    )

    db.add(new_item_model)
    db.flush()

    db.commit()

    log(log.INFO, "Created item [%s] for store [%s]", new_item.name, new_item_model.store_id)
    return s.ItemOut.model_validate(new_item_model)


@item_router.delete(
    "/{item_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Delete item by UUID"""

    item = db.scalar(sa.select(m.Item).where(m.Item.uuid == item_uuid, m.Item.store_id == current_store.id))

    if not item:
        log(log.ERROR, "Item [%s] not found for store [%s]", item_uuid, current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    item.mark_as_deleted()
    db.commit()
    db.refresh(item)

    log(log.INFO, "Deleted item [%s] for store [%s]", item_uuid, current_store.url)
    return None


@item_router.post(
    "{item_uuid}/main_image",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_item_main_image(
    image: s.FileIn,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.post(
    "{item_uuid}/main_video",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_item_main_video(
    video: s.FileIn,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.delete(
    "{item_uuid}/main_image",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_item_main_image(
    image_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.delete(
    "{item_uuid}/main_video",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_item_video(
    video_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.post(
    "/{item_uuid}/image",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def upload_item_image(
    image: Sequence[s.FileIn],
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.delete(
    "/{item_uuid}/image/{image_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_image(
    item_uuid: str,
    image_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.post(
    "/{item_uuid}/document",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def upload_item_document(
    document: s.FileIn,
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@item_router.delete(
    "/{item_uuid}/document/{document_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_document(
    item_uuid: str,
    document_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")
