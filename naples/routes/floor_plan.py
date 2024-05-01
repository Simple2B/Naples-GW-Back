from fastapi import APIRouter, Depends


from naples import models as m, schemas as s
from naples.dependency.user import get_current_user
from naples.logger import log
from naples.dependency.store import get_current_store

floor_plan_router = APIRouter(prefix="/floor_plans", tags=["floor_plans"])


@floor_plan_router.get("/{item_uuid}", response_model=list[s.FloorPlanOut])
def get_floor_plans_for_item(item_uuid: str, current_store: m.Store = Depends(get_current_store)):
    log(log.INFO, "Getting floor plans for item {%s} in store {%s}", item_uuid, current_store)
    return []


@floor_plan_router.post("/", response_model=s.FloorPlanOut)
def create_floor_plan(floor_plan: s.FloorPlanIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Creating floor plan {%s} in store {%s}", floor_plan, current_user.uuid)
    raise NotImplementedError()


@floor_plan_router.put("/{floor_plan_uuid}", response_model=s.FloorPlanOut)
def update_floor_plan(
    floor_plan_uuid: str, floor_plan: s.FloorPlanIn, current_user: m.User = Depends(get_current_user)
):
    log(
        log.INFO,
        "Updating floor plan uuid {%s} with data {%s} in store {%s}",
        floor_plan_uuid,
        floor_plan,
        current_user.uuid,
    )
    raise NotImplementedError()


@floor_plan_router.delete("/{floor_plan_uuid}")
def delete_floor_plan(floor_plan_uuid: str, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Deleting floor plan uuid {%s} in store {%s}", floor_plan_uuid, current_user.uuid)
    raise NotImplementedError()
