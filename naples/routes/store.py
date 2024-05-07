from typing import Sequence, cast
from fastapi import Depends, APIRouter, UploadFile, status, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa

import naples.models as m
import naples.schemas as s
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
    current_user: m.User = Depends(get_current_user),
):
    """Returns the store"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.uuid == store_uuid))
    if not store:
        log(log.ERROR, "Store [%s] not found", store_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store


# TODO: implement this route with Depends from admin
@store_router.get("/", status_code=status.HTTP_200_OK, response_model=s.Stores)
def get_stors(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    query = sa.select(m.Store)
    stores: Sequence[m.Store] = db.scalars(query).all()
    return s.Stores(stores=cast(list, stores))


@store_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.StoreOut)
def create_stote(
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
    # current_store: m.Store = Depends(get_current_user_store),
):
    # log(log.INFO, "Uploading image [%s] for store [%s]", image.filename, current_store.url)
    log(log.INFO, f"THIS IS A TEST ROUTE. TO BE IMPLEMENTED: {image.filename}")

    # return current_store


@store_router.post(
    "/video",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def upload_store_video(
    video: s.FileIn,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@store_router.delete(
    "/image/{image_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_image(
    image_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")


@store_router.delete(
    "/video/{video_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_video(
    video_uuid: str,
    db: Session = Depends(get_db),
    current_store: m.User = Depends(get_current_user_store),
):
    raise NotImplementedError("Not implemented")
