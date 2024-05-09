import sqlalchemy as sa

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from naples.database import get_db
from naples.dependency.user import get_current_user
from naples.logger import log
from naples import schemas as s, models as m


amenities_router = APIRouter(prefix="/amenities", tags=["Amenities"])


@amenities_router.get("", response_model=s.AmenitiesListOut, status_code=status.HTTP_200_OK)
def get_all_amenities(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    log(log.INFO, "User {%s} is fetching all amenities", current_user.uuid)
    amenities = db.scalars(sa.select(m.Amenity).where(m.Amenity.is_deleted == False).order_by(m.Amenity.value))  # noqa: E712
    return s.AmenitiesListOut(items=list(amenities))


@amenities_router.post("/", response_model=s.AmenityOut, status_code=status.HTTP_201_CREATED)
def create_amenity(
    amenity_in: s.AmenityIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    log(log.INFO, "User {%s} is creating amenity {%s}", current_user.uuid, amenity_in.value)
    amenity = m.Amenity(value=amenity_in.value)
    db.add(amenity)
    db.commit()
    db.refresh(amenity)
    return amenity


@amenities_router.delete("/{amenity_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_amenity(
    amenity_uuid: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    log(log.INFO, "User {%s} is deleting amenity {%s}", current_user.uuid, amenity_uuid)
    amenity = db.scalar(sa.select(m.Amenity).where(m.Amenity.uuid == amenity_uuid))
    if not amenity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity not found")
    amenity.is_deleted = True
    db.commit()
    return None
