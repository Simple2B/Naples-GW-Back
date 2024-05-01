from fastapi import APIRouter, Depends

from naples import models as m, schemas as s
from naples.dependency.user import get_current_user
from naples.logger import log
from naples.dependency.store import get_current_store

rates_router = APIRouter(prefix="/rates", tags=["rates"])


@rates_router.get("/{item_uuid}", response_model=list[s.RateOut])
async def get_rates_for_item(item_uuid: str, store: m.Store = Depends(get_current_store)):
    log(log.INFO, "Getting rates for item {%s} in store {%s}", item_uuid, store)
    return []


@rates_router.post("", response_model=s.RateOut)
async def create_rate(rate: s.RateIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Creating rate {%s} in store {%s}", rate, current_user.store)
    raise NotImplementedError()


@rates_router.put("/{rate_uuid}", response_model=s.RateOut)
async def update_rate(rate_uuid: str, rate: s.RateIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Updating rate uuid {%s} with data {%s} in store {%s}", rate_uuid, rate, current_user.store)
    raise NotImplementedError()


@rates_router.delete("/{rate_uuid}")
async def delete_rate(rate_uuid: str, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, "Deleting rate uuid {%s} in store {%s}", rate_uuid, current_user.store)
    raise NotImplementedError()
