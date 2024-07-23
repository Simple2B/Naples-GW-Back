from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, HTTPException
import sqlalchemy as sa

from naples.database import get_db
from naples import models as m, schemas as s
from naples.dependency import get_admin
from naples.logger import log

metadatas_router = APIRouter(prefix="/metadata", tags=["Metadata"])


@metadatas_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.MetadataOut,
)
def get_metadata(
    db: Session = Depends(get_db),
):
    """Get metadata keys"""

    video_url = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == s.MetadataType.VIDEO_COVER_URL.value))
    image_url = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == s.MetadataType.IMAGE_COVER_URL.value))

    return s.MetadataOut(
        video_cover_url=video_url.value if video_url else "",
        image_cover_url=image_url.value if image_url else "",
    )


@metadatas_router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Metadata not found"},
    },
    dependencies=[Depends(get_admin)],
)
def update_metadata(
    data: s.MetadataIn,
    db: Session = Depends(get_db),
):
    """Update metadata"""

    if data.image_cover_url is not None:
        image_url_data = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == s.MetadataType.IMAGE_COVER_URL.value))
        if not image_url_data:
            log(log.ERROR, "Metadata [%s] not found", s.MetadataType.IMAGE_COVER_URL.value)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metadata not found")
        image_url_data.value = data.image_cover_url

    if data.video_cover_url is not None:
        video_url_data = db.scalar(sa.select(m.Metadata).where(m.Metadata.key == s.MetadataType.VIDEO_COVER_URL.value))
        if not video_url_data:
            log(log.ERROR, "Metadata [%s] not found", s.MetadataType.VIDEO_COVER_URL.value)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metadata not found")
        video_url_data.value = data.video_cover_url

    db.commit()

    return
