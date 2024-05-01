from typing import Sequence

# from botocore.exceptions import ClientError
from fastapi import Depends, APIRouter, status, HTTPException  # ,UploadFile, File
from fastapi_pagination import Page, Params, paginate

# from naples.dependency import get_s3_connect
import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples.dependency import get_current_user, get_current_store
from naples.database import get_db

from naples.config import config

CFG = config()


item_router = APIRouter(prefix="/items", tags=["Items"])


@item_router.get(
    "/{item_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemOut,
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
    items: Sequence[s.ItemOut] = [item for item in db_items]

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

# ItemDataIn
def create_item(
    new_item: s.ItemIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
    # s3=Depends(get_s3_connect),
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

    new_item: m.Item = m.Item(
        **new_item.model_dump(exclude={"realtor_uuid", "city_uuid"}),
        realtor_id=realtor.id,
        store_id=store.id,
        city_id=city.id,
    )

    db.add(new_item)
    db.flush()

    # TODO: To be extracted into a separate router logic

    # for file in files:
    #     if not file:
    #         log(log.ERROR, "No file provided")
    #         continue
    #     try:
    #         file.file.seek(0)
    #         s3.upload_fileobj(
    #             file.file,
    #             CFG.AWS_S3_BUCKET_NAME,
    #             f"naples/type=item/user={current_user.uuid}/{store.uuid}/{file.filename}",
    #         )
    #     except ClientError as e:
    #         log(log.ERROR, "Error uploading file to S3 - [%s]", e)
    #         raise HTTPException(status_code=500, detail="Something went wrong")
    #     finally:
    #         file.file.close()

    #     # save to db
    #     new_file: m.File = m.File(
    #         name=file.filename,
    #         original_name=file.filename,
    #         type=file.content_type,
    #         owner_type=s.OwnerType.ITEM.value,
    #         owner_id=new_item.id,
    #         url=f"{CFG.AWS_S3_BUCKET_URL}naples/type=item/user={current_user.uuid}/store={store.uuid}/{file.filename}",
    #     )
    #     db.add(new_file)
    #     log(log.INFO, "Created file [%s] for item [%s]", file.filename, new_item.name)

    db.commit()

    log(log.INFO, "Created item [%s] for store [%s]", new_item.name, new_item.store_id)
    return new_item
