import sqlalchemy as sa

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from naples.database import get_db
from naples.dependency import get_current_user_store, get_current_store
from naples import schemas as s, models as m
from naples.logger import log


member_router = APIRouter(prefix="/members", tags=["Members"])


@member_router.get("", response_model=s.MemberListOut)
def get_members(store: m.Store = Depends(get_current_store)):
    log(log.INFO, "Getting members for store {%s}", store.uuid)
    members = [s.MemberOut.model_validate(member) for member in store.members]
    return s.MemberListOut(items=members)


@member_router.get("/{member_uuid}", response_model=s.MemberOut)
def get_member(member_uuid: str, current_store: m.Store = Depends(get_current_store), db: Session = Depends(get_db)):
    log(log.INFO, "Getting member {%s} for store {%s}", member_uuid, current_store.uuid)

    member = db.scalar(sa.select(m.Member).where(m.Member.uuid == member_uuid))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member not found")

    return s.MemberOut.model_validate(member)


@member_router.post("/", response_model=s.MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(
    member: s.MemberIn, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Creating member {%s} for user {%s}", member, current_store.uuid)
    try:
        member_model = m.Member(**member.model_dump(), store_id=current_store.id)
        db.add(member_model)
        db.commit()
        db.refresh(member_model)
        return s.MemberOut.model_validate(member_model)
    except IntegrityError as e:
        db.rollback()
        log(log.ERROR, "Error creating member {%s} for user {%s} with error {%s}", member, current_store.uuid, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member already exists")


@member_router.put("/{member_uuid}", response_model=s.MemberOut)
def update_member(
    member_uuid: str,
    member: s.MemberIn,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Updating member {%s} with params {%s} for user {%s}", member_uuid, member, current_store.uuid)

    member_model = db.scalar(sa.select(m.Member).where(m.Member.uuid == member_uuid))

    if not member_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member_model.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member not found")

    try:
        member_model.name = member.name
        member_model.email = member.email
        member_model.phone = member.phone
        member_model.instagram_url = member.instagram_url
        member_model.messenger_url = member.messenger_url
        db.commit()
        db.refresh(member_model)
        return s.MemberOut.model_validate(member_model)
    except IntegrityError as e:
        db.rollback()
        log(
            log.ERROR,
            "Error updating member {%s} with params {%s} for user {%s} with error {%s}",
            member_uuid,
            member,
            current_store.uuid,
            e,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad update payload")


@member_router.delete("/{member_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_uuid: str, current_store: s.User = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Deleting member {%s} in store {%s}", member_uuid, current_store.uuid)

    member = db.scalar(sa.select(m.Member).where(m.Member.uuid == member_uuid))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member not found")

    if member.items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member has items")

    member.mark_as_deleted()
    db.commit()


@member_router.post(
    "{member_uuid}/avatar",
    response_model=s.MemberOut,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Member not found"},
    },
)
def upload_member_avatar(
    member_uuid: str,
    image: s.FileIn,
    current_store: m.User = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    raise NotImplementedError("Not implemented")


@member_router.delete(
    "{member_uuid}/avatar",
    response_model=s.MemberOut,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Member not found"},
    },
)
def delete_member_avatar(
    member_uuid: str,
    current_store: m.User = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    raise NotImplementedError("Not implemented")
