import sqlalchemy as sa

from fastapi import Depends, APIRouter, UploadFile, status, HTTPException
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session

from naples.controllers.file import get_file_type
from naples.dependency.s3_client import get_s3_connect
from naples import controllers as c, models as m, schemas as s


from naples.logger import log
from naples.dependency import get_current_user, get_current_user_store
from naples.database import get_db
from naples.utils import get_file_extension


store_router = APIRouter(prefix="/stores", tags=["Stores"])


@store_router.get(
    "/{store_url}",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_store(
    store_url: str,
    db: Session = Depends(get_db),
):
    """Returns the store"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.url == store_url))
    if not store:
        log(log.ERROR, "Store [%s] not found", store_url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store


# TODO: implement this route with Depends from admin
# @store_router.get("/", status_code=status.HTTP_200_OK, response_model=s.Stores)
# def get_stores(
#     db: Session = Depends(get_db),
#     current_user: m.User = Depends(get_current_user),
# ):
#     query = sa.select(m.Store)
#     stores: Sequence[m.Store] = db.scalars(query).all()
#     return s.Stores(stores=cast(list, stores))


@store_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.StoreOut)
def create_store(
    store: s.StoreIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    new_store: m.Store = m.Store(
        **store.model_dump(),
        user_id=current_user.id,
    )
    db.add(new_store)
    db.commit()
    log(log.INFO, "Created store [%s] for user [%s]", new_store.url, new_store.user_id)
    return new_store


@store_router.patch("/", status_code=status.HTTP_200_OK, response_model=s.StoreOut)
def update_store(
    store: s.StoreUpdateIn,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    if store.url is not None:
        log(log.INFO, "Updating url to [%s] for store [%s]", store.url, current_store.url)
        # TODO: implement update of DNS list for server
        current_store.url = store.url
    if store.email is not None:
        log(log.INFO, "Updating email to [%s] for store [%s]", store.email, current_store.url)
        current_store.email = store.email

    if store.instagram_url is not None:
        log(log.INFO, "Updating instagram url to [%s] for store [%s]", store.instagram_url, current_store.url)
        current_store.instagram_url = str(store.instagram_url)

    if store.messenger_url is not None:
        log(log.INFO, "Updating messenger url to [%s] for store [%s]", store.messenger_url, current_store.url)
        current_store.messenger_url = str(store.messenger_url)

    if store.phone is not None:
        log(log.INFO, "Updating phone to [%s] for store [%s]", store.phone, current_store.url)
        current_store.phone = store.phone

    if store.title_value is not None:
        log(log.INFO, "Updating title value to [%s] for store [%s]", store.title_value, current_store.url)
        current_store.title_value = store.title_value

    if store.title_color is not None:
        log(log.INFO, "Updating title color to [%s] for store [%s]", store.title_color.as_hex(), current_store.url)
        current_store.title_color = store.title_color.as_hex()

    if store.title_font_size is not None:
        log(log.INFO, "Updating title font size to [%s] for store [%s]", store.title_font_size, current_store.url)
        current_store.title_font_size = store.title_font_size

    if store.sub_title_value is not None:
        log(log.INFO, "Updating sub title value to [%s] for store [%s]", store.sub_title_value, current_store.url)
        current_store.sub_title_value = store.sub_title_value

    if store.sub_title_color is not None:
        log(
            log.INFO,
            "Updating sub title color to [%s] for store [%s]",
            store.sub_title_color.as_hex(),
            current_store.url,
        )
        current_store.sub_title_color = store.sub_title_color.as_hex()

    if store.sub_title_font_size is not None:
        log(
            log.INFO,
            "Updating sub title font size to [%s] for store [%s]",
            store.sub_title_font_size,
            current_store.url,
        )
        current_store.sub_title_font_size = store.sub_title_font_size

    db.commit()
    db.refresh(current_store)
    log(log.INFO, "Updated store [%s]", current_store.url)
    return current_store


@store_router.post(
    "/main_media",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Store not found"},
    },
)
def upload_store_main_media(
    main_media: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading main media for store [%s]", current_store.url)

    if current_store.main_media and not current_store.main_media.is_deleted:
        log(log.WARNING, "Store [%s] already has a main media. Marking as deleted", current_store.url)
        current_store.main_media.mark_as_deleted()
        db.commit()

    extension = get_file_extension(main_media)

    if not extension:
        log(log.ERROR, "Extension not found for main media [%s]", main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    file_type = get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "File type not supported for main media [%s]", main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not supported")

    main_media_file_model = c.create_file(
        db=db,
        file=main_media,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=file_type,
    )

    current_store.main_media_id = main_media_file_model.id
    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Main media [%s] uploaded for store [%s]", main_media_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/main_media",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_main_media(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting main media for store [%s]", current_store.url)
    if not current_store.main_media:
        log(log.ERROR, "Store [%s] does not have a main media", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a main media")

    current_store.main_media.mark_as_deleted()
    db.commit()

    log(log.INFO, "Main media deleted for store [%s]", current_store.url)


@store_router.post(
    "/logo",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
)
def upload_store_logo(
    logo: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading logo for store [%s]", current_store.url)

    if current_store.logo and not current_store.logo.is_deleted:
        log(log.WARNING, "Store [%s] already has a logo. Marking as deleted", current_store.url)
        current_store.logo.mark_as_deleted()
        db.commit()

    if not logo.content_type == "image/svg+xml":
        log(log.ERROR, "Logo must be of type image/svg+xml. Received [%s]", logo.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo must be of type image/svg+xml")

    logo_file_model = c.create_file(
        db=db,
        file=logo,
        s3_client=s3_client,
        extension="svg",
        store_url=current_store.url,
        file_type=s.FileType.LOGO,
        content_type_override="image/svg+xml",
    )

    current_store.logo_id = logo_file_model.id
    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Logo [%s] uploaded for store [%s]", logo_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/logo",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_logo(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting logo for store [%s]", current_store.url)
    if not current_store.logo:
        log(log.ERROR, "Store [%s] does not have a logo", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a logo")

    current_store.logo.mark_as_deleted()
    db.commit()

    log(log.INFO, "Logo deleted for store [%s]", current_store.url)
