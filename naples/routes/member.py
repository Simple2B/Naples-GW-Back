from fastapi import APIRouter, Depends

from naples.dependency.user import get_current_user
import naples.schemas as s
from naples.logger import log


member_router = APIRouter(prefix="/members", tags=["Members"])


@member_router.get("", response_model=list[s.MemberOut])
def get_members(store_url: str):
    log(log.INFO, "Getting members for store {%s}", store_url)
    return []


@member_router.get("/{member_uuid}", response_model=s.MemberOut)
def get_member(member_uuid: str, current_user: s.User = Depends(get_current_user)):
    log(log.INFO, "Getting member {%s} for user {%s}", member_uuid, current_user)
    raise NotImplementedError()


@member_router.post("", response_model=s.MemberOut)
def create_member(member: s.MemberIn, current_user: s.User = Depends(get_current_user)):
    log(log.INFO, "Creating member {%s} for user {%s}", member, current_user)
    raise NotImplementedError()


@member_router.patch("/{member_uuid}", response_model=s.MemberOut)
def update_member(member_uuid: str, member: s.MemberIn, current_user: s.User = Depends(get_current_user)):
    log(log.INFO, "Updating member {%s} with params {%s} for user {%s}", member_uuid, member, current_user)
    raise NotImplementedError()


@member_router.delete("/{member_uuid}")
def delete_member(member_uuid: str, current_user: s.User = Depends(get_current_user)):
    log(log.INFO, "Deleting member {%s} for user {%s}", member_uuid, current_user)
    raise NotImplementedError()
