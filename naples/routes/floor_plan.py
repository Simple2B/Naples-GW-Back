from mypy_boto3_s3 import S3Client
import sqlalchemy as sa

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session


from naples import models as m, schemas as s, controllers as c
from naples.database import get_db
from naples.dependency import get_user_subscribe
from naples.dependency.get_user_store import get_current_user_store
from naples.dependency.s3_client import get_s3_connect
from naples.logger import log
from naples.dependency.store import get_current_store
from naples.utils import get_file_extension

floor_plan_router = APIRouter(prefix="/floor_plans", tags=["floor_plans"])


@floor_plan_router.get("/{item_uuid}", response_model=s.FloorPlanListOut)
def get_floor_plans_for_item(
    item_uuid: str,
    current_store: m.Store = Depends(get_current_store),
    subscription: m.Subscription = Depends(get_user_subscribe),
):
    log(log.INFO, "Getting floor plans for item {%s} in store {%s}", item_uuid, current_store)

    item = current_store.get_item_by_uuid(item_uuid)

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    items = [s.FloorPlanOut.model_validate(floor_plan) for floor_plan in item.floor_plans]

    log(log.INFO, "Got floor plans for item {%s} in store {%s}", item_uuid, current_store)
    return s.FloorPlanListOut(items=items)


@floor_plan_router.post(
    "/{item_uuid}",
    response_model=s.FloorPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def create_floor_plan(
    item_uuid: str,
    image: UploadFile,
    current_store: m.Store = Depends(get_current_user_store),
    db: Session = Depends(get_db),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Creating floor plan in store {%s}", current_store.uuid)

    item = current_store.get_item_by_uuid(item_uuid)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    floor_plan = m.FloorPlan(item_id=item.id)
    db.add(floor_plan)
    db.commit()
    db.refresh(floor_plan)

    log(log.INFO, "Created floor plan {%s} in store {%s}", floor_plan, current_store.uuid)

    extension = get_file_extension(image)

    file_model = c.create_file(
        file=image,
        db=db,
        s3_client=s3_client,
        file_type=s.FileType.IMAGE,
        store_url=current_store.url,
        extension=extension,
    )

    floor_plan.image_id = file_model.id
    db.commit()

    return s.FloorPlanOut.model_validate(floor_plan)


@floor_plan_router.delete("/{floor_plan_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_floor_plan(
    floor_plan_uuid: str, current_store: m.Store = Depends(get_current_user_store), db: Session = Depends(get_db)
):
    log(log.INFO, "Deleting floor plan uuid {%s} in store {%s}", floor_plan_uuid, current_store.uuid)

    floor_plan = db.scalar(sa.select(m.FloorPlan).filter(m.FloorPlan.uuid == floor_plan_uuid))
    if not floor_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan not found")
    if floor_plan.item.store_id != current_store.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own floor plans")

    for marker in floor_plan.markers:
        marker.is_deleted = True

    if floor_plan.image:
        floor_plan.image.mark_as_deleted()

    floor_plan.is_deleted = True
    db.commit()

    log(log.INFO, "Deleted floor plan uuid {%s} in store {%s}", floor_plan_uuid, current_store.uuid)


# this is the new endpoint
# @floor_plan_router.post("/{floor_plan_uuid}/image", status_code=status.HTTP_201_CREATED, response_model=s.FloorPlanOut)
# def upload_floor_plan_image(
#     floor_plan_uuid: str,
#     image: UploadFile,
#     current_store: m.Store = Depends(get_current_user_store),
#     db: Session = Depends(get_db),
#     s3_client: S3Client = Depends(get_s3_connect),
# ):
#     log(log.INFO, "Uploading image for floor plan uuid {%s} in store {%s}", floor_plan_uuid, current_store.uuid)

#     floor_plan = db.scalar(sa.select(m.FloorPlan).filter(m.FloorPlan.uuid == floor_plan_uuid))
#     if not floor_plan:
#         log(log.ERROR, "Floor plan not found")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan not found")

#     if floor_plan.item.store_id != current_store.id:
#         log(log.ERROR, "You can only upload images for your own floor plans")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="You can only upload images for your own floor plans"
#         )

#     if floor_plan.image:
#         log(log.INFO, "Deleting old image for floor plan {%s}", floor_plan_uuid)
#         floor_plan.image.mark_as_deleted()
#         db.commit()

#     log(log.INFO, "Creating new image for floor plan {%s}", floor_plan_uuid)

#     extension = get_file_extension(image)

#     file_model = c.create_file(
#         file=image,
#         db=db,
#         s3_client=s3_client,
#         file_type=s.FileType.IMAGE,
#         store_url=current_store.url,
#         extension=extension,
#     )

#     floor_plan.image_id = file_model.id
#     db.commit()

#     return s.FloorPlanOut.model_validate(floor_plan)
