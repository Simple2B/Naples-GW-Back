from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
from moto import mock_aws
from mypy_boto3_ses import SESClient


from naples import schemas as s, models as m

from naples.config import config


CFG = config("testing")


@mock_aws
def test_create_admin_contact_request(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    ses: SESClient,
):
    admin = full_db.scalar(select(m.User).where(m.User.role == s.UserRole.ADMIN.value))
    assert admin

    ses.verify_email_address(EmailAddress=admin.email)
    ses.verify_email_address(EmailAddress=CFG.MAIL_DEFAULT_SENDER)

    req_payload = s.AdminContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="john_doe@buu.com",
        phone="1234567890",
        message="Hello, I would like to know more about this service",
    )

    ses.verify_email_address(EmailAddress=req_payload.email)

    res = client.post("/api/admin_contact_requests/", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 201
    contact_request = s.AdminContactRequestOut.model_validate(res.json())

    contact_request_model = full_db.scalar(select(m.AdminContactRequest))
    assert contact_request_model

    assert contact_request.first_name == contact_request_model.first_name
    assert contact_request.last_name == contact_request_model.last_name
    assert contact_request.email == contact_request_model.email


def test_get_admin_contact_requests(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    admin_headers: dict[str, str],
):
    request_one = s.AdminContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this service",
    )

    res_one = client.post("/api/admin_contact_requests/", content=request_one.model_dump_json(), headers=headers)
    assert res_one.status_code == 201

    request_two = s.AdminContactRequestIn(
        first_name="Den",
        last_name="Brown",
        email="def@def.com",
        phone="1234567890",
        message="Hello, I would like to know more about this service",
    )

    res_two = client.post("/api/admin_contact_requests/", content=request_two.model_dump_json(), headers=headers)
    assert res_two.status_code == 201

    res = client.get("/api/admin_contact_requests/", headers=admin_headers)
    assert res.status_code == 200

    contact_requests = s.AdminContactRequestListOut.model_validate(res.json())

    admin_contact_requests = full_db.execute(select(m.AdminContactRequest)).scalars().all()

    assert len(admin_contact_requests) == len(contact_requests.contact_requests)

    assert contact_requests.contact_requests[0].first_name == request_one.first_name
    assert contact_requests.contact_requests[1].email == request_two.email

    res_den = client.get("/api/admin_contact_requests", headers=admin_headers, params={"search": "Den"})
    assert res_den.status_code == 200
    user = s.AdminContactRequestListOut.model_validate(res_den.json())
    assert len(user.contact_requests) == 1
    assert user.contact_requests[0].first_name == "Den"

    john_model = full_db.scalar(select(m.AdminContactRequest).where(m.AdminContactRequest.email == "abc@abc.com"))
    assert john_model

    john_model.status = s.ContactRequestStatus.PROCESSED.value
    full_db.commit()

    processed = client.get(
        "/api/admin_contact_requests",
        headers=admin_headers,
        params={"status": s.AdminContactRequestStatus.PROCESSED.value},
    )
    assert processed.status_code == 200
    processed_requests = s.AdminContactRequestListOut.model_validate(processed.json())

    assert len(processed_requests.contact_requests) == 1
    assert processed_requests.contact_requests[0].first_name == "John"


def test_update_admin_contact_request_status(
    client: TestClient,
    full_db: Session,
    headers: dict[str, str],
    admin_headers: dict[str, str],
):
    admin = full_db.scalar(select(m.User).where(m.User.role == s.UserRole.ADMIN.value))
    assert admin

    payload = s.AdminContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this service",
    )

    res = client.post("/api/admin_contact_requests/", content=payload.model_dump_json(), headers=headers)

    assert res.status_code == 201

    contact_request = s.AdminContactRequestOut.model_validate(res.json())
    assert contact_request.status == s.AdminContactRequestStatus.CREATED

    res = client.put(
        f"/api/admin_contact_requests/{contact_request.uuid}",
        content=s.AdminContactRequestUpdateIn(status=s.AdminContactRequestStatus.PROCESSED).model_dump_json(),
        headers=admin_headers,
    )

    assert res.status_code == 200
    updated_contact_request = s.AdminContactRequestOut.model_validate(res.json())
    assert updated_contact_request.status == s.AdminContactRequestStatus.PROCESSED


def test_delete_admin_contact_request(
    client: TestClient,
    headers: dict[str, str],
    admin_headers: dict[str, str],
):
    contact_request = s.AdminContactRequestIn(
        first_name="John",
        last_name="Doe",
        email="abc@abc.com",
        phone="1234567890",
        message="Hello, I would like to know more about this service",
    )
    response = client.post("/api/admin_contact_requests/", content=contact_request.model_dump_json(), headers=headers)
    assert response.status_code == 201

    db_contact_request = s.AdminContactRequestOut.model_validate(response.json())

    res = client.delete(
        f"/api/admin_contact_requests/{db_contact_request.uuid}",
        headers=admin_headers,
    )
    assert res.status_code == 204

    assert db_contact_request.is_deleted is False

    res = client.get("/api/admin_contact_requests", headers=admin_headers)
    assert res.status_code == 200
    response_contact_requests = s.AdminContactRequestListOut.model_validate(res.json())
    assert len(response_contact_requests.contact_requests) == 0
