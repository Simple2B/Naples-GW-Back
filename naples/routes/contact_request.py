import sqlalchemy as sa
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from naples import schemas as s, models as m, dependency as d
from naples.logger import log
from naples.database import get_db


contact_request_router = APIRouter(prefix="/contact_requests", tags=["Contact Requests"])


@contact_request_router.post(
    "/",
    response_model=s.ContactRequestOut,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Item not found"}},
)
async def create_contact_request(
    contact_request: s.ContactRequestIn,
    store: m.Store = Depends(d.get_current_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Creating contact request for store {%s}", store.uuid)
    item = None
    if contact_request.item_uuid:
        item = db.scalar(sa.select(m.Item).where(m.Item.uuid == contact_request.item_uuid))
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    contact_request = m.ContactRequest(
        **contact_request.model_dump(exclude={"store_uuid", "item_uuid"}),
        store_id=store.id,
        item_id=item.id if item else None,
    )
    db.add(contact_request)
    db.commit()
    db.refresh(contact_request)
    log(log.INFO, "Contact request {%s} created for store {%s}", contact_request.uuid, store.uuid)
    return contact_request


@contact_request_router.get("/", response_model=s.ContactRequestListOut)
async def get_contact_requests(
    store: m.Store = Depends(d.get_current_user_store),
    db: Session = Depends(get_db),
    search: str | None = None,
    status: s.ContactRequestStatus | None = None,
):
    log(log.INFO, "Getting contact requests for store {%s}. Search: {%s}. Status: {%s}", store.uuid, search, status)
    stmt = (
        sa.select(m.ContactRequest)
        .where(sa.and_(m.ContactRequest.store_id == store.id, m.ContactRequest.is_deleted.is_(False)))
        .order_by(m.ContactRequest.created_at.desc())
    )
    if search:
        items = db.scalars(
            sa.select(m.Item).where(m.Item.store_id == store.id).where(m.Item.name.ilike(f"%{search}%"))
        ).all()
        item_ids = [item.id for item in items]

        stmt = stmt.where(
            sa.or_(
                m.ContactRequest.first_name.ilike(f"%{search}%"),
                m.ContactRequest.last_name.ilike(f"%{search}%"),
                m.ContactRequest.email.ilike(f"%{search}%"),
                m.ContactRequest.item_id.in_(item_ids),
            )
        )
    if status:
        stmt = stmt.where(m.ContactRequest.status == status.value)
    contact_requests = db.scalars(stmt).all()
    res = s.ContactRequestListOut(items=list(contact_requests))
    log(log.INFO, "Found {%s} contact requests for store {%s}", len(res.items), store.uuid)
    return res


@contact_request_router.put(
    "/{contact_request_uuid}",
    response_model=s.ContactRequestOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Contact request not found"}},
)
async def update_contact_request_status(
    contact_request_uuid: str,
    data: s.ContactRequestUpdateIn,
    store: m.Store = Depends(d.get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Updating contact request status for store {%s}", store.uuid)
    contact_request = db.scalar(sa.select(m.ContactRequest).where(m.ContactRequest.uuid == contact_request_uuid))
    if not contact_request:
        log(log.ERROR, "Contact request {%s} not found", contact_request_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact request not found")

    if contact_request.store_id != store.id:
        log(log.ERROR, "Contact request {%s} does not belong to store {%s}", contact_request.uuid, store.uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact request not found")

    # TODO: Ability to limit downgrading status (ask the client if such functionality is needed)
    # if contact_request.status != s.ContactRequestStatus.CREATED.value and data.status == s.ContactRequestStatus.CREATED:
    #     log(log.ERROR, "Contact request {%s} is already processed", contact_request.uuid)
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status downgrade is not allowed")

    contact_request.status = data.status.value
    db.commit()
    db.refresh(contact_request)
    log(log.INFO, "Contact request {%s} status updated for store {%s}", contact_request.uuid, store.uuid)
    return contact_request


@contact_request_router.delete("/{contact_request_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_request(
    contact_request_uuid: str,
    store: m.Store = Depends(d.get_current_user_store),
    db: Session = Depends(get_db),
):
    log(log.INFO, "Deleting contact request {%s} for store {%s}", contact_request_uuid, store.uuid)
    contact_request = db.scalar(sa.select(m.ContactRequest).where(m.ContactRequest.uuid == contact_request_uuid))
    if not contact_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact request not found")

    contact_request.is_deleted = True
    db.commit()
    log(log.INFO, "Contact request {%s} deleted for store {%s}", contact_request.uuid, store.uuid)
