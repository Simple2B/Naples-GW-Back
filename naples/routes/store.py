from typing import Sequence, cast
from fastapi import Depends, APIRouter, status, HTTPException

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
# from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user
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
    log(log.INFO, "Created store [%s] for user [%s]", new_store.name, new_store.user_id)
    return new_store
