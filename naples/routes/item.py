from typing import Annotated, Sequence
from datetime import datetime

from fastapi import Depends, APIRouter, File, Form, UploadFile, status, HTTPException
from fastapi_pagination import Page, Params, paginate
from mypy_boto3_s3 import S3Client

from naples.controllers.file import get_file_type
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
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.ItemOut],
    responses={
        404: {"description": "Store not found"},
        403: {"description": "Invalid URL"},
        400: {"description": "Store URL is not provided"},
    },
)
def get_published_items(
    city_uuid: str | None = None,
    adults: int = 0,
    rent_length: s.RentalLength | None = None,
    check_in: datetime | None = None,
    check_out: datetime | None = None,
    name: str | None = None,
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
            m.Item.stage == s.ItemStage.ACTIVE.value,
        )
    )

    if city_uuid:
        city: m.City | None = db.scalar(sa.select(m.City).where(m.City.uuid == city_uuid))
        assert city, f"City with UUID [{city_uuid}] not found"
        stmt = stmt.where(m.Item.city_id == city.id)

    if adults:
        stmt = stmt.where(m.Item.adults >= adults)

    if rent_length:
        if rent_length == s.RentalLength.NIGHTLY:
            stmt = stmt.where(m.Item.nightly.is_(True))
        elif rent_length == s.RentalLength.MONTHLY:
            stmt = stmt.where(m.Item.monthly.is_(True))
        elif rent_length == s.RentalLength.ANNUAL:
            stmt = stmt.where(m.Item.annual.is_(True))

    if check_in:
        stmt = stmt.where(
            m.Item._booked_dates.any(sa.and_(m.BookedDate.from_date == check_in, m.BookedDate.is_deleted.is_(False)))
        )

    if check_out:
        stmt = stmt.where(
            m.Item._booked_dates.any(sa.and_(m.BookedDate.to_date == check_out, m.BookedDate.is_deleted.is_(False)))
        )

    if name:
        stmt = stmt.where(m.Item.name.ilike(f"%{name}%"))

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [s.ItemOut.model_validate(item) for item in db_items]

    log(log.INFO, "Got [%s] items for store [%s]", len(items), current_store.url)

    return paginate(items, params)


@item_router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.ItemOut],
    responses={
        404: {"description": "Store not found"},
        403: {"description": "Invalid URL"},
        400: {"description": "Store URL is not provided"},
    },
)
def get_all_items(
    name: str | None = None,
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

    if name:
        stmt = stmt.where(m.Item.name.ilike(f"%{name}%"))

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [s.ItemOut.model_validate(item) for item in db_items]

    log(log.INFO, "Got [%s] items for store [%s]", len(items), current_store.url)

    return paginate(items, params)


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
    "/filters/data",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemsFilterDataOut,
)
def get_filters_data(
    db: Session = Depends(get_db),
    current_user_store: m.Store = Depends(get_current_store),
):
    """Get data for filter items"""

    cities_idx = [
        item.city_id
        for item in current_user_store.items
        if not item.is_deleted and item.stage == s.ItemStage.ACTIVE.value
    ]

    cities = db.scalars(sa.select(m.City).where(m.City.id.in_(cities_idx))).all()
    adults = max(
        [
            item.adults
            for item in current_user_store.items
            if not item.is_deleted and item.stage == s.ItemStage.ACTIVE.value
        ],
        default=0,
    )

    return s.ItemsFilterDataOut(locations=list(cities), adults=adults)


@item_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def create_item(
    new_item: s.ItemIn,  # ItemDataIn
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


@item_router.patch(
    "/{item_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def update_item(
    item_uuid: str,
    item_data: s.ItemUpdateIn,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Update item by UUID"""

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found for store [%s]", item_uuid, current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item_data.city_uuid is not None:
        city = db.scalar(sa.select(m.City).where(m.City.uuid == item_data.city_uuid))
        if not city:
            log(log.ERROR, "City [%s] not found", item_data.city_uuid)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
        log(log.INFO, "City [%s] was updated for item [%s]", city.name, item_uuid)
        item.city_id = city.id

    if item_data.realtor_uuid is not None:
        realtor = db.scalar(sa.select(m.Member).where(m.Member.uuid == item_data.realtor_uuid))
        if not realtor:
            log(log.ERROR, "Realtor [%s] not found", item_data.realtor_uuid)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Realtor not found")
        log(log.INFO, "Realtor [%s] was updated for item [%s]", realtor.email, item_uuid)
        item.realtor_id = realtor.id

    if item_data.name is not None:
        log(log.INFO, "Name [%s] was updated for item [%s]", item_data.name, item_uuid)
        item.name = item_data.name

    if item_data.description is not None:
        log(log.INFO, "Description [%s] was updated for item [%s]", item_data.description, item_uuid)
        item.description = item_data.description

    if item_data.latitude is not None:
        log(log.INFO, "Latitude [%s] was updated for item [%s]", item_data.latitude, item_uuid)
        item.latitude = item_data.latitude

    if item_data.longitude is not None:
        log(log.INFO, "Longitude [%s] was updated for item [%s]", item_data.longitude, item_uuid)
        item.longitude = item_data.longitude

    if item_data.stage is not None:
        log(log.INFO, "Stage [%s] was updated for item [%s]", item_data.stage, item_uuid)
        item.stage = item_data.stage.value

    if item_data.size is not None:
        log(log.INFO, "Size [%s] was updated for item [%s]", item_data.size, item_uuid)
        item.size = item_data.size

    if item_data.bedrooms_count is not None:
        log(log.INFO, "Bedrooms count [%s] was updated for item [%s]", item_data.bedrooms_count, item_uuid)
        item.bedrooms_count = item_data.bedrooms_count

    if item_data.bathrooms_count is not None:
        log(log.INFO, "Bathrooms count [%s] was updated for item [%s]", item_data.bathrooms_count, item_uuid)
        item.bathrooms_count = item_data.bathrooms_count

    if item_data.airbnb_url is not None:
        log(log.INFO, "Airbnb URL [%s] was updated for item [%s]", item_data.airbnb_url, item_uuid)
        item.airbnb_url = str(item_data.airbnb_url)

    if item_data.vrbo_url is not None:
        log(log.INFO, "VRBO URL [%s] was updated for item [%s]", item_data.vrbo_url, item_uuid)
        item.vrbo_url = str(item_data.vrbo_url)

    if item_data.expedia_url is not None:
        log(log.INFO, "Expedia URL [%s] was updated for item [%s]", item_data.expedia_url, item_uuid)
        item.expedia_url = str(item_data.expedia_url)

    if item_data.adults is not None:
        log(log.INFO, "Adults [%s] was updated for item [%s]", item_data.adults, item_uuid)
        item.adults = item_data.adults

    if item_data.show_rates is not None:
        log(log.INFO, "Show rates [%s] was updated for item [%s]", item_data.show_rates, item_uuid)
        item.show_rates = item_data.show_rates

    if item_data.show_fees is not None:
        log(log.INFO, "Show fees [%s] was updated for item [%s]", item_data.show_fees, item_uuid)
        item.show_fees = item_data.show_fees

    if item_data.show_external_urls is not None:
        log(log.INFO, "Show external URLs [%s] was updated for item [%s]", item_data.show_external_urls, item_uuid)
        item.show_external_urls = item_data.show_external_urls

    if item_data.nightly is not None:
        log(log.INFO, "Nightly [%s] was updated for item [%s]", item_data.nightly, item_uuid)
        item.nightly = item_data.nightly

    if item_data.monthly is not None:
        log(log.INFO, "Monthly [%s] was updated for item [%s]", item_data.monthly, item_uuid)
        item.monthly = item_data.monthly

    if item_data.annual is not None:
        log(log.INFO, "Annual [%s] was updated for item [%s]", item_data.annual, item_uuid)
        item.annual = item_data.annual

    db.commit()
    db.refresh(item)

    log(log.INFO, "Updated item [%s] for store [%s]", item_uuid, current_store.url)
    return item


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
    "/{item_uuid}/main_media",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_item_main_media(
    item_uuid: str,
    main_media: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading main media for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if item.main_media:
        log(log.INFO, "Deleting previous main media for item [%s]", item_uuid)
        item.main_media.mark_as_deleted()

    extension = get_file_extension(main_media)

    file_type = get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "Unknown file extension [%s]", extension)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown file extension")

    item_model = c.create_file(
        file=main_media,
        db=db,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=file_type,
    )

    item.main_media_id = item_model.id
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main media for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/main_media",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_item_main_media(
    item_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting main media for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if not item.main_media:
        log(log.ERROR, "Item [%s] has no main media", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item has no main media")

    item.main_media.mark_as_deleted()
    db.commit()
    db.refresh(item)

    log(log.INFO, "Main media for item [%s] was deleted", item_uuid)


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
    document: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
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

    document_model.title = title

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


@item_router.post(
    "/{item_uuid}/amenities/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def add_item_amenities(
    item_uuid: str,
    amenities: s.ItemAmenitiesIn,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Adding amenities for item [%s]", item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    for amenity_uuid in amenities.amenities_uuids:
        amenity = db.scalar(sa.select(m.Amenity).where(m.Amenity.uuid == amenity_uuid))

        if not amenity:
            log(log.ERROR, "Amenity [%s] not found", amenity_uuid)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity not found")

        item._amenities.append(amenity)
    db.commit()
    db.refresh(item)

    log(log.INFO, "Amenities for item [%s] were added", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/amenity/{amenity_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_amenity(
    item_uuid: str,
    amenity_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting amenity [%s] for item [%s]", amenity_uuid, item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    amenity = next((a for a in item._amenities if a.uuid == amenity_uuid), None)

    if not amenity:
        log(log.ERROR, "Amenity [%s] not found for item [%s]", amenity_uuid, item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity not found")

    item._amenities.remove(amenity)
    db.commit()

    log(log.INFO, "Amenity [%s] for item [%s] was deleted", amenity_uuid, item_uuid)
