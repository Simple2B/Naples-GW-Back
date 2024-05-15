from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.testclient import TestClient

from naples import schemas as s, models as m


def test_create_member(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    req_payload = s.MemberIn(
        name="Test Member",
        email="test@test.com",
        phone="1234567890",
        instagram_url="https://instagram.com/test",
        messenger_url="https://messenger.com/test",
    )

    res = client.post("/api/members/", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 201

    member = s.MemberOut.model_validate(res.json())
    member_model = full_db.scalar(select(m.Member).where(m.Member.email == req_payload.email))

    assert member_model
    assert member.name == member_model.name
    assert member.email == member_model.email


def test_duplicate_member(client: TestClient, full_db: Session, headers: dict[str, str]):
    store = full_db.scalar(select(m.Store))
    assert store

    req_payload = s.MemberIn(
        name="Test Member",
        email="test@test.com",
        phone="1234567890",
        instagram_url="https://instagram.com/test",
        messenger_url="https://messenger.com/test",
    )

    res = client.post("/api/members/", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 201

    res = client.post("/api/members/", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 400


def test_get_members(client: TestClient, full_db: Session):
    store = full_db.scalar(select(m.Store))
    assert store

    res = client.get("/api/members", params={"store_url": store.url})
    assert res.status_code == 200

    members = s.MemberListOut.model_validate(res.json())
    assert members.items


def test_get_member_details(client: TestClient, full_db: Session):
    member_model = full_db.scalar(select(m.Member))
    assert member_model

    res = client.get(f"/api/members/{member_model.uuid}", params={"store_url": member_model.store.url})

    assert res.status_code == 200

    member = s.MemberOut.model_validate(res.json())
    assert member

    assert member.email == member_model.email


def test_update_member(client: TestClient, full_db: Session, headers: dict[str, str]):
    member = full_db.scalar(select(m.Member))
    assert member

    req_payload = s.MemberIn(
        name="Updated Member",
        email="bubu@bubu.com",
        phone="1234567890",
        instagram_url="https://instagram.com/test",
        messenger_url="",
    )

    res = client.put(f"/api/members/{member.uuid}", content=req_payload.model_dump_json(), headers=headers)
    assert res.status_code == 200

    updated_member = s.MemberOut.model_validate(res.json())
    assert updated_member

    assert updated_member.name == req_payload.name
    assert updated_member.email == req_payload.email
    assert updated_member.phone == req_payload.phone
    assert updated_member.instagram_url == req_payload.instagram_url
    assert updated_member.messenger_url == req_payload.messenger_url
    assert member.title == "Realtor"
    assert updated_member.title == member.title


def test_delete_member(client: TestClient, full_db: Session, headers: dict[str, str]):
    member = full_db.scalar(select(m.Member))
    assert member

    assert member.items

    res = client.delete(f"/api/members/{member.uuid}", headers=headers)
    assert res.status_code == 409

    for item in member.items:
        del_res = client.delete(f"/api/items/{item.uuid}", headers=headers)
        assert del_res.status_code == 204

    res = client.delete(f"/api/members/{member.uuid}", headers=headers)
    assert res.status_code == 204

    member = full_db.scalar(select(m.Member).where(m.Member.uuid == member.uuid))
    assert member and member.is_deleted


def test_upload_member_avatar(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        member_model = full_db.scalar(select(m.Member))
        assert member_model

        res = client.post(
            f"/api/members/{member_model.uuid}/avatar",
            files={"avatar": ("test.jpg", f, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        member = s.MemberOut.model_validate(res.json())
        assert member.avatar_url

        assert member_model.avatar_url == member.avatar_url


def test_update_member_avatar(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    with open("tests/house_example.png", "rb") as f:
        member_model = full_db.scalar(select(m.Member))
        assert member_model

        res = client.post(
            f"/api/members/{member_model.uuid}/avatar",
            files={"avatar": ("test.jpg", f, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        member = s.MemberOut.model_validate(res.json())
        assert member.avatar_url

        assert member_model.avatar_url == member.avatar_url

        update_res = client.post(
            f"/api/members/{member_model.uuid}/avatar",
            files={"avatar": ("test_2.jpg", f, "image/jpeg")},
            headers=headers,
        )

        assert update_res.status_code == 201

        updated_member = s.MemberOut.model_validate(update_res.json())
        assert updated_member.avatar_url

        assert updated_member.avatar_url != member.avatar_url

        assert member_model.avatar_url == updated_member.avatar_url


def test_delete_avatar(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    member_model = full_db.scalar(select(m.Member))
    assert member_model

    with open("tests/house_example.png", "rb") as f:
        res = client.post(
            f"/api/members/{member_model.uuid}/avatar",
            files={"avatar": ("test.jpg", f, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        member = s.MemberOut.model_validate(res.json())
        assert member.avatar_url

        assert member_model.avatar_url == member.avatar_url

        del_res = client.delete(f"/api/members/{member_model.uuid}/avatar", headers=headers)
        assert del_res.status_code == 204

        full_db.refresh(member_model)

        assert member_model.avatar_url == ""
