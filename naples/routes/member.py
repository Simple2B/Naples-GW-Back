from mypy_boto3_s3 import S3Client
import sqlalchemy as sa
import filetype

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from naples.database import get_db
from naples.dependency import get_current_user_store, get_current_store
from naples import schemas as s, models as m, controllers as c
from naples.dependency.s3_client import get_s3_connect
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
    "/{member_uuid}/avatar",
    response_model=s.MemberOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Member not found"},
    },
)
def upload_member_avatar(
    member_uuid: str,
    avatar: UploadFile,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading avatar for member {%s} in store {%s}", member_uuid, current_store.uuid)
    member = db.scalar(sa.select(m.Member).where(m.Member.uuid == member_uuid))
    if not member:
        log(log.ERROR, "Member not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.store_id != current_store.id:
        log(log.ERROR, "Member not found")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member not found")

    extension = filetype.guess_extension(avatar.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", avatar.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    if member.avatar:
        log(log.INFO, "Deleting old avatar for member {%s}", member_uuid)
        member.avatar.mark_as_deleted()
        db.commit()

    log(log.INFO, "Creating new avatar for member {%s}", member_uuid)
    file_model = c.create_file(
        file=avatar,
        db=db,
        s3_client=s3_client,
        file_type=s.FileType.AVATAR,
        store_url=current_store.url,
        extension=extension,
    )

    member.avatar_id = file_model.id
    db.commit()
    db.refresh(member)

    log(log.INFO, "Avatar uploaded for member {%s}", member_uuid)
    return s.MemberOut.model_validate(member)


@member_router.delete(
    "/{member_uuid}/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Member not found"},
    },
)
def delete_member_avatar(
    member_uuid: str,
    current_store: m.User = Depends(get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Deleting avatar for member {%s} in store {%s}", member_uuid, current_store.uuid)
    member = db.scalar(sa.select(m.Member).where(m.Member.uuid == member_uuid))
    if not member:
        log(log.ERROR, "Member not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.store_id != current_store.id:
        log(log.ERROR, "Member not found")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member not found")

    if not member.avatar:
        log(log.ERROR, "Member does not have an avatar")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member does not have an avatar")

    member.avatar.mark_as_deleted()
    db.commit()

    log(log.INFO, "Avatar deleted for member {%s}", member_uuid)
