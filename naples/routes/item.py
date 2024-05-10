from typing import Sequence
from datetime import datetime

from fastapi import Depends, APIRouter, UploadFile, status, HTTPException
from fastapi_pagination import Page, Params, paginate
from mypy_boto3_s3 import S3Client

from naples.dependency.s3_client import get_s3_connect
import naples.models as m
import naples.schemas as s
from naples import controllers as c
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session

from naples.dependency import get_current_user, get_current_store, get_current_user_store
from naples.database import get_db

from naples.config import config
from naples.utils import get_file_extension

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
    adults: int = 0,
    rent_type: s.ItemType | None = None,
    check_in: datetime | None = None,
    check_out: datetime | None = None,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_store),
):
    """Get items by filters and pagination"""

    log(log.INFO, "Getting items for store [%s]", current_store.url)

    stmt = sa.select(m.Item).where(
        sa.and_(
            m.Item.is_deleted.is_(False),
            m.Item.store_id == current_store.id,
        )
    )

    if city_uuid:
        city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == city_uuid))
        assert city, f"City with UUID [{city_uuid}] not found"
        stmt = stmt.where(m.Item.city_id == city.id)

    if adults:
        stmt = stmt.where(m.Item.adults >= adults)

    # if rent_type:
    #     if rent_type == s.ItemType.NIGHTLY:
    #         stmt = stmt.where(m.Item._rates.any(m.Rate. == s.ItemType.NIGHTLY))

    if check_in:
        stmt = stmt.where(
            m.Item._booked_dates.any(sa.and_(m.BookedDate.date >= check_in, m.BookedDate.is_deleted.is_(False)))
        )

    if check_out:
        stmt = stmt.where(
            m.Item._booked_dates.any(sa.and_(m.BookedDate.date <= check_out, m.BookedDate.is_deleted.is_(False)))
        )

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [s.ItemOut.model_validate(item) for item in db_items]

    log(log.INFO, "Got [%s] items for store [%s]", len(items), current_store.url)

    return paginate(items, params)


@item_router.get(
    "/filters/data",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemsFilterDataOut,
)
def get_filters_data(
    db: Session = Depends(get_db),
    current_user_store: m.Store = Depends(get_current_store),
):
    """Get data for filter items"""

    cities_idx = [item.city_id for item in current_user_store.items if not item.is_deleted]

    cities = db.scalars(sa.select(m.City).where(m.City.id.in_(cities_idx))).all()
    adults = max([item.adults for item in current_user_store.items if not item.is_deleted], default=0)

    return s.ItemsFilterDataOut(locations=list(cities), adults=adults)


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
    "/{item_uuid}/main_image",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_item_main_image(
    item_uuid: str,
    image: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading main image for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if item.image:
        log(log.INFO, "Deleting previous main image for item [%s]", item_uuid)
        item.image.mark_as_deleted()

    extension = get_file_extension(image)

    item_model = c.create_file(
        file=image,
        db=db,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.IMAGE,
    )

    item.image_id = item_model.id
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main image for item [%s] was uploaded", item_uuid)

    return s.ItemOut.model_validate(item)


@item_router.post(
    "/{item_uuid}/main_video",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_item_main_video(
    item_uuid: str,
    video: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading main video for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.video:
        log(log.INFO, "Deleting previous main video for item [%s]", item_uuid)
        item.video.mark_as_deleted()

    extension = get_file_extension(video)

    item_model = c.create_file(
        file=video,
        db=db,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.VIDEO,
        s3_client=s3_client,
    )

    item.video_id = item_model.id
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main video for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/main_image",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_item_main_image(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting main image for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not item.image:
        log(log.ERROR, "Item [%s] has no main image", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item has no main image")

    item.image.mark_as_deleted()
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main image for item [%s] was deleted", item_uuid)


@item_router.delete(
    "/{item_uuid}/main_video",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_item_video(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting main video for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not item.video:
        log(log.ERROR, "Item [%s] has no main video", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item has no main video")

    item.video.mark_as_deleted()
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main video for item [%s] was deleted", item_uuid)


@item_router.post(
    "/{item_uuid}/image/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def upload_item_image(
    image: UploadFile,
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading image for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    extension = get_file_extension(image)

    item_model = c.create_file(
        file=image,
        db=db,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.IMAGE,
        s3_client=s3_client,
    )

    item._images.append(item_model)
    db.commit()
    db.refresh(item)

    log(log.INFO, "Image for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/image/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_image(
    item_uuid: str,
    image_url: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting image [%s] for item [%s]", image_url, item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    image = next((i for i in item._images if i.url == image_url), None)

    if not image:
        log(log.ERROR, "Image [%s] not found for item [%s]", image_url, item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    image.mark_as_deleted()
    db.commit()
    db.refresh(item)

    log(log.INFO, "Image [%s] for item [%s] was deleted", image_url, item_uuid)


@item_router.post(
    "/{item_uuid}/document",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def upload_item_document(
    document: UploadFile,
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading document for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    extension = get_file_extension(document)

    document_model = c.create_file(
        file=document,
        db=db,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.ATTACHMENT,
        s3_client=s3_client,
    )

    item._documents.append(document_model)
    db.commit()
    db.refresh(item)

    log(log.INFO, "Document for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/document",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_document(
    item_uuid: str,
    document_url: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting document [%s] for item [%s]", document_url, item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    document = next((d for d in item.documents if d.url == document_url), None)

    if not document:
        log(log.ERROR, "Document [%s] not found for item [%s]", document_url, item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.mark_as_deleted()
    db.commit()

    log(log.INFO, "Document [%s] for item [%s] was deleted", document_url, item_uuid)


# TODO: implement update_item
