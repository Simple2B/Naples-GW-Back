from fastapi import APIRouter, Depends

from naples import schemas as s, models as m
from naples.logger import log
from naples.dependency.user import get_current_user


floor_plan_marker_router = APIRouter(prefix="/plan_markers", tags=["plan_markers"])


@floor_plan_marker_router.post("/", response_model=s.FloorPlanMarkerOut)
def create_floor_plan_marker(floor_plan_marker: s.FlorPlanMarkerIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Creating floor plan marker {%s} in store {%s}", floor_plan_marker, current_user.store)
    raise NotImplementedError()


@floor_plan_marker_router.put("/{floor_plan_marker_uuid}", response_model=s.FloorPlanMarkerOut)
def update_floor_plan_marker(
    floor_plan_marker_uuid: str, floor_plan_marker: s.FlorPlanMarkerIn, current_user: m.User = Depends(get_current_user)
):
    log(
        log.INFO,
        "Updating floor plan marker uuid {%s} with data {%s} in store {%s}",
        floor_plan_marker_uuid,
        floor_plan_marker,
        current_user.store,
    )
    raise NotImplementedError()


@floor_plan_marker_router.delete("/{floor_plan_marker_uuid}")
def delete_floor_plan_marker(floor_plan_marker_uuid: str, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Deleting floor plan marker uuid {%s} in store {%s}", floor_plan_marker_uuid, current_user.store)
    raise NotImplementedError()
