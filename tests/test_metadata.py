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
    data_1 = s.Metadata(
        key="cover_url_image",
        value="https://example.com/image.jpg",
    )

    response = client.post(
        "/api/metadatas/",
        headers=admin_headers,
        json=data_1.model_dump(),
    )

    assert response.status_code == 200

    data_2 = s.Metadata(
        key="cover_url_image",
        value="https://example.com/image.jpg",
    )

    response = client.post(
        "/api/metadatas/",
        headers=admin_headers,
        json=data_2.model_dump(),
    )

    assert response.status_code == 400

    data_3 = s.Metadata(
        key="cover_url_video",
        value="https://example.com/video.mp4",
    )

    response = client.post(
        "/api/metadatas/",
        headers=admin_headers,
        json=data_3.model_dump(),
    )

    assert response.status_code == 200

    metadata_db = db.scalars(sa.select(m.Metadata)).all()

    assert len(metadata_db) == 2

    response = client.get(
        "/api/metadatas/",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == [
        data_1.model_dump(),
        data_3.model_dump(),
    ]

    update_data = s.Metadata(
        key=data_2.key,
        value="https://example.com/image2.jpg",
    )

    response = client.patch(
        "/api/metadatas/",
        headers=admin_headers,
        json=update_data.model_dump(),
    )

    assert response.status_code == 200

    not_found_data = s.Metadata(
        key="key_not_found",
        value="https://example.com/image2.jpg",
    )

    response = client.patch(
        "/api/metadatas/",
        headers=admin_headers,
        json=not_found_data.model_dump(),
    )

    assert response.status_code == 404
