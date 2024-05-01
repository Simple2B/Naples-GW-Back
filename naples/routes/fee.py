from fastapi import APIRouter, Depends

from naples.dependency.store import get_current_store
from naples.logger import log
from naples import schemas as s, models as m
from naples.dependency.user import get_current_user


fee_router = APIRouter(prefix="/fee", tags=["Fee"])


@fee_router.get("/{item_uuid}", response_model=list[s.FeeOut])
async def get_fees_for_item(item_uuid: str, current_store: m.Store = Depends(get_current_store)):
    log(
        log.INFO,
        "Getting fee {%s} for user {%s}",
    )
    raise NotImplementedError


@fee_router.post("/", response_model=s.FeeOut, status_code=201)
async def create_fee(data: s.FeeIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, f"Creating fee {data} for user {current_user}")
    raise NotImplementedError


@fee_router.put("/{fee_uuid}", response_model=s.FeeOut)
async def update_fee(fee_uuid: str, data: s.FeeIn, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, f"Updating fee {fee_uuid} with data {data} for user {current_user}")
    raise NotImplementedError


@fee_router.delete("/{fee_uuid}")
async def delete_fee(fee_uuid: str, current_user: m.User = Depends(get_current_user)):
    log(log.INFO, f"Deleting fee {fee_uuid} for user {current_user}")
    raise NotImplementedError
