from time import sleep
from typing import Annotated, Sequence
from datetime import datetime

from fastapi import Depends, APIRouter, File, Form, Query, UploadFile, status, HTTPException
from fastapi_pagination import Page, Params, paginate
import sqlalchemy as sa
from sqlalchemy.orm import Session
from mypy_boto3_s3 import S3Client

from naples import models as m, schemas as s
from naples.dependency import (
    get_current_user,
    get_current_store,
    get_current_user_store,
    get_user_subscribe,
    get_s3_connect,
)
from naples import controllers as c
from naples.database import get_db
from naples.routes.utils import (
    check_user_subscription_max_active_items,
    check_user_subscription_max_items,
)
from naples.utils import get_file_extension, get_link_type
from naples.logger import log


from naples.config import config

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
    dependencies=[Depends(get_user_subscribe)],
)
def get_published_items(
    rent_length: Annotated[list[s.RentalLength], Query()] = [],
    city: str | None = None,
    adults: int = 0,
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

    if adults:
        stmt = stmt.where(m.Item.adults >= adults)

    if rent_length:
        r_length = [r.value for r in rent_length]
        log(log.INFO, "Rent length [%s]", r_length)
        conditions = []
        if s.RentalLength.NIGHTLY.value in r_length:
            conditions.append(m.Item.nightly.is_(True))
        if s.RentalLength.MONTHLY.value in r_length:
            conditions.append(m.Item.monthly.is_(True))
        if s.RentalLength.ANNUAL.value in r_length:
            conditions.append(m.Item.annual.is_(True))

        if conditions:
            stmt = stmt.where(sa.or_(*conditions))

    if name:
        stmt = stmt.where(m.Item.name.ilike(f"%{name}%"))

    db_items: Sequence[m.Item] = db.scalars(stmt).all()
    items: Sequence[s.ItemOut] = [s.ItemOut.model_validate(item) for item in db_items]

    if check_out and check_in:
        # items_out = [item for item in items if is_available(item, check_in.date(), check_out.date())]
        items_out = [
            item
            for item in items
            if all(check_in >= booked.to_date or check_out <= booked.from_date for booked in item.booked_dates)
        ]
        return paginate(items_out, params)

    if city is not None:
        items_by_city: Sequence[s.ItemOut] = [
            s.ItemOut.model_validate(item) for item in db_items if item.location.city == city
        ]
        return paginate(items_by_city, params)

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
    dependencies=[Depends(get_user_subscribe)],
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

    db_items: Sequence[m.Item] = db.scalars(stmt.order_by(m.Item.created_at)).all()
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
    dependencies=[Depends(get_user_subscribe)],
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
    dependencies=[Depends(get_user_subscribe)],
)
def get_filters_data(
    db: Session = Depends(get_db),
    current_user_store: m.Store = Depends(get_current_store),
):
    """Get data for filter items"""

    location_cities = [
        item.location.city
        for item in current_user_store.items
        if item.stage == s.ItemStage.ACTIVE.value and not item.is_deleted
    ]

    unique_cities = set(location_cities)

    adults = max(
        [
            item.adults
            for item in current_user_store.items
            if not item.is_deleted and item.stage == s.ItemStage.ACTIVE.value
        ],
        default=0,
    )

    return s.ItemsFilterDataOut(cities=list(unique_cities), adults=adults)


@item_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemOut,
    responses={
        404: {"description": "Store not found"},
        403: {"description": "Max items limit reached"},
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

    res = check_user_subscription_max_items(store, db)

    if not res:
        log(log.ERROR, "Max items limit reached")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max items limit reached")

    realtor: m.Member | None = db.scalar(sa.select(m.Member).where(m.Member.uuid == new_item.realtor_uuid))

    if not realtor or realtor.store_id != store.id:
        log(log.ERROR, "Realtor [%s] not found", new_item.realtor_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Realtor not found")

    new_item_model: m.Item = m.Item(
        **new_item.model_dump(
            exclude={
                "realtor_uuid",
                "city",
                "state",
                "address",
                "latitude",
                "longitude",
            }
        ),
        realtor_id=realtor.id,
        store_id=store.id,
    )

    db.add(new_item_model)
    db.flush()

    db.commit()

    log(log.INFO, "Created item [%s] for store [%s]", new_item.name, new_item_model.store_id)

    # add location for item
    item_location: m.Location = m.Location(
        address=new_item.address,
        city=new_item.city,
        state=new_item.state,
        item_id=new_item_model.id,
    )

    db.add(item_location)
    db.flush()

    db.commit()

    log(
        log.INFO,
        "Created location [%s] for item [%s]",
        item_location.city,
        new_item_model.id,
    )

    if new_item.longitude is not None:
        log(
            log.INFO,
            "Add longitude [%s] to location [%s] ",
            new_item.longitude,
            item_location.city,
        )
        item_location.longitude = new_item.longitude
        db.commit()

    if new_item.latitude is not None:
        log(
            log.INFO,
            "Add latitude [%s] to location [%s] ",
            new_item.latitude,
            item_location.city,
        )
        item_location.latitude = new_item.latitude
        db.commit()

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

    if item_data.city is not None:
        # TODO: is it necessary to do such a check for the location? is there any sense in this?
        # location = db.scalar(sa.select(m.Location).where(m.Location.id == item.location.id))

        # if not location:
        #     log(log.ERROR, "Location [%s] not found", item.location.id)
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location not found")

        item.location.city = item_data.city

        log(log.ERROR, "City [%s] was updated for item [%s] ", item_data.city, item_uuid)

    if item_data.address is not None:
        item.location.address = item_data.address

        log(log.ERROR, "Address [%s] was updated for item [%s] ", item_data.address, item_uuid)

    if item_data.state is not None:
        item.location.state = item_data.state

        log(log.ERROR, "State [%s] was updated for item [%s] ", item_data.state, item_uuid)

    if item_data.longitude is not None:
        item.location.longitude = item_data.longitude

        log(log.ERROR, "Longitude [%s] was updated for item [%s] ", item_data.longitude, item_uuid)

    if item_data.latitude is not None:
        item.location.latitude = item_data.latitude

        log(log.ERROR, "Latitude [%s] was updated for item [%s] ", item_data.longitude, item_uuid)

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

    if item_data.stage is not None:
        res = check_user_subscription_max_active_items(current_store, item, db)
        if not res:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Max active items limit reached")
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

    if item_data.images_urls is not None:
        log(log.INFO, "Images urls [%s] was updated for item [%s]", len(item_data.images_urls), item_uuid)

        for url_image in item_data.images_urls:
            # find files and update data of each file
            key_url = url_image.replace(CFG.AWS_S3_BUCKET_URL, "")
            file: m.File | None = db.scalar(sa.select(m.File).where(m.File.key == key_url))
            # update date
            if file:
                file.updated_at = datetime.now()
                db.commit()
                db.refresh(file)
                sleep(0.05)

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

    file_type = c.get_file_type(extension)

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


@item_router.post(
    "/{item_uuid}/video",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
    },
)
def upload_item_video(
    item_uuid: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Upload video for item by UUID"""

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    extension = get_file_extension(file)

    file_type = c.get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "Unknown file extension [%s]", extension)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown file extension")

    item_model = c.create_file(
        file=file,
        db=db,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=file_type,
    )

    item._videos.append(item_model)

    db.commit()
    db.refresh(item)

    log(log.INFO, "Video for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/video",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_video(
    item_uuid: str,
    video_url: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Delete video for item by url"""

    log(log.INFO, "Deleting video [%s] for item [%s]", video_url, item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    video = next((v for v in item._videos if v.url == video_url), None)

    if not video:
        log(log.ERROR, "Video [%s] not found for item [%s]", video_url, item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    video.mark_as_deleted()
    db.commit()

    log(log.INFO, "Video [%s] for item [%s] was deleted", video_url, item_uuid)


@item_router.post(
    "/{item_uuid}/link",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ItemDetailsOut,
    responses={
        404: {"description": "Item not found"},
        400: {"description": "Unknown link type"},
    },
)
def upload_item_link(
    item_uuid: str,
    data: s.LinkIn,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Upload link for item by UUID"""

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # get type of link
    link_type = get_link_type(data.url)

    if link_type == s.LinkType.UNKNOWN.value:
        log(log.ERROR, "Unknown link type [%s]", data.url)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown link type")

    item_model = m.Link(
        type=link_type,
        url=data.url,
    )

    item._links.append(item_model)

    db.commit()
    db.refresh(item)

    log(log.INFO, "Link for item [%s] was uploaded", item_uuid)

    return s.ItemDetailsOut.model_validate(item)


@item_router.delete(
    "/{item_uuid}/link",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Item not found"},
    },
)
def delete_item_link(
    item_uuid: str,
    link: str,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Delete link for item by url"""

    log(log.INFO, "Deleting link [%s] for item [%s]", link, item_uuid)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        log(log.ERROR, "Item [%s] not found", item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    db_link = next((db_link for db_link in item._links if db_link.url == link), None)

    if not db_link:
        log(log.ERROR, "Link [%s] not found for item [%s]", link, item_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    db_link.is_deleted = True
    db_link.deleted_at = datetime.now()
    db.commit()

    log(log.INFO, "Link [%s] for item [%s] was deleted", link, item_uuid)
