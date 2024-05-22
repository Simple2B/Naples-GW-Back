from fastapi.testclient import TestClient
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_create_floor_plan_with_markers(
    client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client
):
    item = full_db.scalar(select(m.Item))

    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())

        assert plan_data.uuid

        marker_payload = s.FloorPlanMarkerIn(x=0.5, y=0.5, floor_plan_uuid=plan_data.uuid)

        res = client.post("/api/plan_markers/", content=marker_payload.model_dump_json(), headers=headers)

        assert res.status_code == 201

        marker = s.FloorPlanMarkerOut.model_validate(res.json())
        assert marker.uuid

        res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})
        assert res.status_code == 200

        plans = s.FloorPlanListOut.model_validate(res.json())

        assert len(plans.items) == 1
        plan = plans.items[0]

        assert plan.uuid == plan_data.uuid
        assert plan.markers

        assert plan.markers[0].uuid == marker.uuid
        assert plan.markers[0].x == marker.x


def test_update_marker(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())
        assert plan_data.img_url

        marker_payload = s.FloorPlanMarkerIn(x=0.5, y=0.5, floor_plan_uuid=plan_data.uuid)

        res = client.post("/api/plan_markers/", content=marker_payload.model_dump_json(), headers=headers)

        marker = s.FloorPlanMarkerOut.model_validate(res.json())

        marker_update_payload = s.FloorPlanMarkerIn(x=0.6, y=0.6, floor_plan_uuid=plan_data.uuid)

        res = client.put(
            f"/api/plan_markers/{marker.uuid}", content=marker_update_payload.model_dump_json(), headers=headers
        )
        assert res.status_code == 200

        updated_marker = s.FloorPlanMarkerOut.model_validate(res.json())
        assert updated_marker.x == marker_update_payload.x


def test_delete_marker(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    # Delete a FloorPlanMarker and verify the response
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())

        marker_payload = s.FloorPlanMarkerIn(x=0.5, y=0.5, floor_plan_uuid=plan_data.uuid)

        res = client.post("/api/plan_markers/", content=marker_payload.model_dump_json(), headers=headers)
        marker = s.FloorPlanMarkerOut.model_validate(res.json())

        res = client.delete(f"/api/plan_markers/{marker.uuid}", headers=headers)
        assert res.status_code == 204

        deleted_marker = full_db.scalar(select(m.FloorPlanMarker).where(m.FloorPlanMarker.uuid == marker.uuid))
        assert deleted_marker and deleted_marker.is_deleted

        plan_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

        plans = s.FloorPlanListOut.model_validate(plan_res.json())

        assert len(plans.items) == 1
        plan = plans.items[0]

        assert not plan.markers


def test_delete_floor_plan(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    # Delete a FloorPlan and verify the response
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_2", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())

        res = client.delete(f"/api/floor_plans/{plan_data.uuid}", headers=headers)
        assert res.status_code == 204

        deleted_plan = full_db.scalar(select(m.FloorPlan).where(m.FloorPlan.uuid == plan_data.uuid))
        assert deleted_plan and deleted_plan.is_deleted

        plan_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

        plans = s.FloorPlanListOut.model_validate(plan_res.json())

        assert not plans.items


def test_upload_floor_plan_image(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_2", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())
        assert plan_data.img_url


def test_update_floor_plan_image(client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client):
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())
        assert plan_data.img_url

        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_2", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        updated_floor_plan = s.FloorPlanOut.model_validate(res.json())
        assert updated_floor_plan.img_url != plan_data.img_url


def test_upload_floor_plan_markers_images(
    client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client
):
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_2", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())
        assert plan_data.uuid

        with open("tests/house_example.png", "rb") as image_file:
            marker_payload = s.FloorPlanMarkerIn(x=0.5, y=0.5, floor_plan_uuid=plan_data.uuid)

            res = client.post("/api/plan_markers/", content=marker_payload.model_dump_json(), headers=headers)

            assert res.status_code == 201

            marker = s.FloorPlanMarkerOut.model_validate(res.json())

            res = client.post(
                f"/api/plan_markers/{marker.uuid}/image",
                files={"image": ("test_image_1", image_file, "image/jpeg")},
                headers=headers,
            )
            assert res.status_code == 201

            res = client.post(
                f"/api/plan_markers/{marker.uuid}/image",
                files={"image": ("test_image_2", image_file, "image/jpeg")},
                headers=headers,
            )

            assert res.status_code == 201

            plans_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

            plans = s.FloorPlanListOut.model_validate(plans_res.json())

            marker = plans.items[1].markers[0]

            assert len(marker.images) == 2


def test_delete_floor_plan_marker_image(
    client: TestClient, full_db: Session, headers: dict[str, str], s3_client: S3Client
):
    item = full_db.scalar(select(m.Item))
    assert item

    with open("tests/house_example.png", "rb") as image_file:
        res = client.post(
            f"/api/floor_plans/{item.uuid}",
            files={"image": ("test_image_1", image_file, "image/jpeg")},
            headers=headers,
        )

        assert res.status_code == 201

        plan_data = s.FloorPlanOut.model_validate(res.json())
        assert plan_data.uuid

        marker_payload = s.FloorPlanMarkerIn(x=0.5, y=0.5, floor_plan_uuid=plan_data.uuid)

        res = client.post("/api/plan_markers/", content=marker_payload.model_dump_json(), headers=headers)
        assert res.status_code == 201

        marker = s.FloorPlanMarkerOut.model_validate(res.json())

        with open("tests/house_example.png", "rb") as image_file:
            res = client.post(
                f"/api/plan_markers/{marker.uuid}/image",
                files={"image": ("test_image_1", image_file, "image/jpeg")},
                headers=headers,
            )
            assert res.status_code == 201

            res = client.post(
                f"/api/plan_markers/{marker.uuid}/image",
                files={"image": ("test_image_2", image_file, "image/jpeg")},
                headers=headers,
            )

            assert res.status_code == 201

            plans_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

            plans = s.FloorPlanListOut.model_validate(plans_res.json())

            marker = plans.items[0].markers[0]

            assert len(marker.images) == 2

            res = client.delete(
                f"/api/plan_markers/{marker.uuid}/image/",
                headers=headers,
                params={"image_url": marker.images[0]},
            )
            assert res.status_code == 204

            plans_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

            plans = s.FloorPlanListOut.model_validate(plans_res.json())

            marker = plans.items[0].markers[0]

            assert len(marker.images) == 1
