import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, HTTPException

from naples import schemas as s, models as m
from naples.database import get_db
from naples.dependency.get_user_store import get_current_user_store
from naples.logger import log


floor_plan_marker_router = APIRouter(prefix="/plan_markers", tags=["plan_markers"])


@floor_plan_marker_router.post("/", response_model=s.FloorPlanMarkerOut, status_code=status.HTTP_201_CREATED)
def create_floor_plan_marker(
    floor_plan_marker: s.FloorPlanMarkerIn,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Creating floor plan marker {%s} in store {%s}", floor_plan_marker, current_store.uuid)

    floor_plan = db.scalar(sa.select(m.FloorPlan).where(m.FloorPlan.uuid == floor_plan_marker.floor_plan_uuid))

    if not floor_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan not found")

    if floor_plan.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Floor plan does not belong to store")

    marker = m.FloorPlanMarker(
        x=floor_plan_marker.x,
        y=floor_plan_marker.y,
        floor_plan_id=floor_plan.id,
    )
    db.add(marker)
    db.commit()
    db.refresh(marker)

    log(log.INFO, "Created floor plan marker {%s} in store {%s}", floor_plan_marker, current_store.uuid)

    return s.FloorPlanMarkerOut.model_validate(marker)


@floor_plan_marker_router.put("/{floor_plan_marker_uuid}", response_model=s.FloorPlanMarkerOut)
def update_floor_plan_marker(
    floor_plan_marker_uuid: str,
    floor_plan_marker: s.FloorPlanMarkerIn,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(
        log.INFO,
        "Updating floor plan marker uuid {%s} with data {%s} in store {%s}",
        floor_plan_marker_uuid,
        floor_plan_marker,
        current_store.uuid,
    )

    marker = db.scalar(sa.select(m.FloorPlanMarker).where(m.FloorPlanMarker.uuid == floor_plan_marker_uuid))

    if not marker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan marker not found")

    if marker.floor_plan.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Floor plan marker does not belong to store")

    marker.x = floor_plan_marker.x
    marker.y = floor_plan_marker.y
    db
    db.commit()
    db.refresh(marker)

    log(log.INFO, "Updated floor plan marker uuid {%s} in store {%s}", floor_plan_marker_uuid, current_store.uuid)

    return s.FloorPlanMarkerOut.model_validate(marker)


@floor_plan_marker_router.delete("/{floor_plan_marker_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_floor_plan_marker(
    floor_plan_marker_uuid: str, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Deleting floor plan marker uuid {%s} in store {%s}", floor_plan_marker_uuid, current_store.uuid)

    marker = db.scalar(sa.select(m.FloorPlanMarker).where(m.FloorPlanMarker.uuid == floor_plan_marker_uuid))

    if not marker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan marker not found")

    if marker.floor_plan.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Floor plan marker does not belong to store")

    marker.is_deleted = True
    db.commit()

    log(log.INFO, "Deleted floor plan marker uuid {%s} in store {%s}", floor_plan_marker_uuid, current_store.uuid)


@floor_plan_marker_router.post("/{floor_plan_marker_uuid}/image", status_code=status.HTTP_201_CREATED)
def upload_floor_plan_marker_image(
    floor_plan_marker_uuid: str,
    image: s.FileIn,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    raise NotImplementedError("Not implemented")


@floor_plan_marker_router.delete("/{floor_plan_marker_uuid}/image/{image_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_floor_plan_marker_image(
    floor_plan_marker_uuid: str,
    image_uuid: str,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    raise NotImplementedError("Not implemented")
