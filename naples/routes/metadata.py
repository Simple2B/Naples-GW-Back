from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, HTTPException
import sqlalchemy as sa

from naples.database import get_db
from naples import models as m, schemas as s
from naples.dependency import get_current_user, get_admin
from naples.logger import log

metadatas_router = APIRouter(prefix="/metadata", tags=["Metadata"])


@metadatas_router.get(
    "/keys",
    status_code=status.HTTP_200_OK,
    response_model=list[s.MetadataType],
)
def get_metadata_keys(
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Get metadata keys"""

    return [metadata for metadata in s.MetadataType]


@metadatas_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.Metadata,
)
def get_metadata(
    key_data: s.MetadataType,
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Get metadata by key"""

    metadata = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == key_data.value))

    if not metadata:
        log(log.INFO, "Metadata [%s] not found ", key_data)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found",
        )

    return s.Metadata.model_validate(metadata)


# @metadatas_router.post(
#     "/",
#     status_code=status.HTTP_200_OK,
#     response_model=s.Metadata,
#     responses={
#         status.HTTP_400_BAD_REQUEST: {"description": "Metadata already present"},
#     },
# )
# def save_metadatas(
#     data: s.Metadata,
#     db: Session = Depends(get_db),
#     curent_user: m.User = Depends(get_current_user),
#     admin: m.User = Depends(get_admin),
# ):
#     """Save metadata"""

#     db_metadata = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == data.key))

#     if db_metadata:
#         log(log.INFO, "Metadata {%s} is already present", data.key)
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Metadata {data.key} is already present",
#         )

#     metadata = m.Metadata(**data.model_dump())

#     db.add(metadata)
#     db.commit()

#     return s.Metadata.model_validate(metadata)


@metadatas_router.patch(
    "/update/{key}",
    status_code=status.HTTP_200_OK,
    response_model=s.Metadata,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Metadata not found"},
    },
)
def update_metadata(
    key: s.MetadataType,
    data: s.MetadataIn,
    db: Session = Depends(get_db),
    curent_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Update metadata"""

    metadata_db: m.Metadata | None = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == key.value))

    if not metadata_db:
        log(log.INFO, "Metadata {%s} not found", key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadata {key} not found",
        )

    metadata_db.value = data.value
    db.commit()
    db.refresh(metadata_db)

    return s.Metadata.model_validate(metadata_db)
