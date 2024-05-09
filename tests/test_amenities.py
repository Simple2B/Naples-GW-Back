from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


from naples import schemas as s, models as m


def test_create_amenity(client: TestClient, full_db: Session, headers: dict[str, str]):
    amenity_payload = s.AmenityIn(value="Test Amenity")
    response = client.post(
        "/api/amenities/",
        content=amenity_payload.model_dump_json(),
        headers=headers,
    )
    assert response.status_code == 201

    amenity = s.AmenityOut.model_validate(response.json())
    assert amenity.value == "Test Amenity"
    assert amenity.uuid


def test_get_all_amenities(client: TestClient, full_db: Session, headers: dict[str, str]):
    full_db.add_all([m.Amenity(value="Test Amenity 1"), m.Amenity(value="Test Amenity 2")])
    full_db.commit()

    response = client.get("/api/amenities", headers=headers)
    assert response.status_code == 200

    amenities = s.AmenitiesListOut.model_validate(response.json())
    assert len(amenities.items) == 2
    assert amenities.items[1].value == "Test Amenity 2"
    assert amenities.items[0].uuid


def test_delete_amenity(client: TestClient, full_db: Session, headers: dict[str, str]):
    amenity = m.Amenity(value="Test Amenity")
    full_db.add(amenity)
    full_db.commit()
    full_db.refresh(amenity)

    response = client.delete(f"/api/amenities/{amenity.uuid}", headers=headers)
    assert response.status_code == 204

    amenity_check = full_db.get(m.Amenity, amenity.id)
    assert amenity_check and amenity_check.is_deleted

    all_res = client.get("/api/amenities", headers=headers)
    amenities = s.AmenitiesListOut.model_validate(all_res.json())
    assert len(amenities.items) == 0
