import sqlalchemy as sa
import filetype

from fastapi import Depends, APIRouter, UploadFile, status, HTTPException
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session

from naples.dependency.s3_client import get_s3_connect
from naples import controllers as c, models as m, schemas as s


from naples.logger import log
from naples.dependency import get_current_user, get_current_user_store
from naples.database import get_db


store_router = APIRouter(prefix="/stores", tags=["Stores"])


@store_router.get(
    "/{store_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_store(
    store_uuid: str,
    db: Session = Depends(get_db),
):
    """Returns the store"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.uuid == store_uuid))
    if not store:
        log(log.ERROR, "Store [%s] not found", store_uuid)
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


@store_router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_store_image(
    image: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading image [%s] for store [%s]", image.filename, current_store.url)

    if current_store.image and not current_store.image.is_deleted:
        log(log.ERROR, "Store [%s] already has an image. Marking as deleted", current_store.url)
        current_store.image.mark_as_deleted()
        db.commit()

    extension = filetype.guess_extension(image.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", image.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    image_file_model = c.create_file(
        db=db,
        file=image,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.IMAGE,
    )

    current_store.image_id = image_file_model.id

    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Image [%s] uploaded for store [%s]", image_file_model.name, current_store.url)

    return current_store


@store_router.post(
    "/video",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_store_video(
    video: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading video for store [%s]", current_store.url)

    if current_store.video and not current_store.video.is_deleted:
        log(log.ERROR, "Store [%s] already has a video. Marking as deleted", current_store.url)
        current_store.video.mark_as_deleted()
        db.commit()

    extension = filetype.guess_extension(video.file)

    if not extension:
        log(log.ERROR, "Extension not found for video [%s]", video.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    video_file_model = c.create_file(
        db=db,
        file=video,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=s.FileType.VIDEO,
    )

    current_store.video_id = video_file_model.id
    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Video [%s] uploaded for store [%s]", video_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/image",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_image(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting image for store [%s]", current_store.url)
    if not current_store.image:
        log(log.ERROR, "Store [%s] does not have an image", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have an image")

    current_store.image.mark_as_deleted()
    db.commit()

    log(log.INFO, "Image deleted for store [%s]", current_store.url)


@store_router.delete(
    "/video",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_video(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting video for store [%s]", current_store.url)
    if not current_store.video:
        log(log.ERROR, "Store [%s] does not have a video", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a video")

    current_store.video.mark_as_deleted()
    db.commit()

    log(log.INFO, "Video deleted for store [%s]", current_store.url)
