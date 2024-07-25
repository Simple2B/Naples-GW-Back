from fastapi.testclient import TestClient
import sqlalchemy as sa

from sqlalchemy.orm import Session


from naples import schemas as s
import naples.models as m
from naples.config import config


CFG = config("testing")


#  save cover urls (metadata) for template (only admin can update)
def test_save_get_metadata(
    client: TestClient,
    db: Session,
    admin_headers: dict[str, str],
    test_data: s.TestData,
):
    response = client.get(
        "/api/metadata",
        headers=admin_headers,
    )

    assert response.status_code == 200

    for metadata in s.MetadataType:
        new_metadata = m.Metadata(key=metadata.value, value="")

        db.add(new_metadata)
    db.commit()

    metadata_db = db.scalars(sa.select(m.Metadata)).all()
    assert metadata_db
    assert len(metadata_db) == 7

    update_data = s.MetadataIn(image_cover_url="image cover url")

    response = client.patch(
        "/api/metadata",
        headers=admin_headers,
        json=update_data.model_dump(),
    )

    assert response.status_code == 200
