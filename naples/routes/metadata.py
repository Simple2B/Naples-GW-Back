from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, HTTPException
import sqlalchemy as sa

from naples.database import get_db
from naples import models as m, schemas as s
from naples.dependency import get_current_user, get_admin
from naples.logger import log

metadatas_router = APIRouter(prefix="/metadatas", tags=["Metadatas"])


@metadatas_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[s.Metadata],
)
def get_metadatas(
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Get all metadata"""

    metadatas = db.execute(sa.select(m.Metadata)).scalars().all()

    return [s.Metadata.model_validate(metadata) for metadata in metadatas]


@metadatas_router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.Metadata,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Metadata already present"},
    },
)
def save_metadatas(
    data: s.Metadata,
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Save metadata"""

    db_metadata = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == data.key))

    if db_metadata:
        log(log.INFO, "Metadata {%s} is already present", data.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metadata {data.key} is already present",
        )

    metadata = m.Metadata(**data.model_dump())

    db.add(metadata)
    db.commit()

    return s.Metadata.model_validate(metadata)


@metadatas_router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Metadata not found"},
    },
)
def update_metadata(
    data: s.Metadata,
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Update metadata"""

    metadata_db: m.Metadata | None = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == data.key))

    if not metadata_db:
        log(log.INFO, "Metadata {%s} not found", data.key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata {data.key} not found",
        )

    metadata_db.value = data.value
    db.commit()
    return
