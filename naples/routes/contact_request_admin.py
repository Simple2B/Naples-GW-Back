from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples import schemas as s, models as m, dependency as d
from naples.logger import log
from naples.database import get_db


admin_contact_request_router = APIRouter(prefix="/admin_contact_requests", tags=["Contact Requests for Admin"])


@admin_contact_request_router.post(
    "/",
    response_model=s.AdminContactRequestOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Admin not found"},
    },
)
async def admin_create_contact_request(
    contact_request: s.AdminContactRequestIn,
    admin: m.User = Depends(d.get_user_admin),
    db: Session = Depends(get_db),
):
    """Create a contact request for admin"""

    log(log.INFO, "Creating contact request for admin {%s}", admin.uuid)

    contact_request = m.AdminContactRequest(
        **contact_request.model_dump(),
        admin_id=admin.id,
    )
    db.add(contact_request)
    db.commit()
    db.refresh(contact_request)

    log(log.INFO, "Contact request {%s} created for admin {%s}", contact_request.uuid, admin.uuid)
    return contact_request


@admin_contact_request_router.get(
    "/",
    response_model=s.AdminContactRequestListOut,
)
async def get_admin_contact_requests(
    db: Session = Depends(get_db),
    admin: m.User = Depends(d.get_admin),
    search: str | None = None,
    status: s.AdminContactRequestStatus | None = None,
):
    """Get all contact requests for admin"""

    stmt = sa.select(m.AdminContactRequest).where(
        sa.and_(m.AdminContactRequest.admin_id == admin.id, m.ContactRequest.is_deleted.is_(False))
    )
    if search:
        stmt = stmt.where(
            sa.or_(
                m.AdminContactRequest.name.ilike(f"%{search}%"),
                m.AdminContactRequest.email.ilike(f"%{search}%"),
            )
        )
    if status:
        stmt = stmt.where(m.AdminContactRequest.status == status.value)
    contact_requests = db.scalars(stmt).all()
    res = s.AdminContactRequestListOut(items=list(contact_requests))
    log(log.INFO, "Contact requests for admin {%s} fetched", admin.uuid)
    return res


@admin_contact_request_router.put(
    "/{contact_request_uuid}",
    response_model=s.AdminContactRequestOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Contact request for admin not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Status downgrade is not allowed"},
    },
    dependencies=[Depends(d.get_admin)],
)
async def update_admin_contact_request_status(
    contact_request_uuid: str,
    data: s.ContactRequestUpdateIn,
    db: Session = Depends(get_db),
):
    """Update the status of a contact request"""

    contact_request = db.scalar(
        sa.select(m.AdminContactRequest).where(m.AdminContactRequest.uuid == contact_request_uuid)
    )

    if not contact_request:
        log(log.ERROR, "Contact request for admin {%s} not found", contact_request_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact request for admin not found")

    if (
        contact_request.status != s.AdminContactRequestStatus.CREATED.value
        and data.status == s.AdminContactRequestStatus.CREATED
    ):
        log(log.ERROR, "Contact request for admin {%s} is already processed", contact_request.uuid)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status downgrade is not allowed")

    contact_request.status = data.status.value
    db.commit()
    db.refresh(contact_request)

    log(log.INFO, "Contact request for admin {%s} updated", contact_request.uuid)

    return contact_request


@admin_contact_request_router.delete(
    "/{contact_request_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(d.get_admin)],
)
async def delete_admin_contact_request(
    contact_request_uuid: str,
    db: Session = Depends(get_db),
):
    """Delete a contact request for admin"""

    contact_request = db.scalar(
        sa.select(m.AdminContactRequest).where(
            m.AdminContactRequest.uuid == contact_request_uuid,
        )
    )
    if not contact_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact request for admin not found")

    contact_request.is_deleted = True
    db.commit()
    log(log.INFO, "Contact request for admin {%s} deleted", contact_request.uuid)
