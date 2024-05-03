from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select


from naples import schemas as s, models as m


def test_create_floor_plan_with_markers(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item
    plan_payload = s.FloorPlanIn(
        item_uuid=item.uuid,
    )

    res = client.post("/api/floor_plans/", content=plan_payload.model_dump_json(), headers=headers)
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


def test_update_marker(client: TestClient, full_db: Session, headers: dict[str, str]):
    item = full_db.scalar(select(m.Item))
    assert item
    plan_payload = s.FloorPlanIn(
        item_uuid=item.uuid,
    )

    res = client.post("/api/floor_plans/", content=plan_payload.model_dump_json(), headers=headers)

    plan_data = s.FloorPlanOut.model_validate(res.json())

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


def test_delete_marker(client: TestClient, full_db: Session, headers: dict[str, str]):
    # Delete a FloorPlanMarker and verify the response
    item = full_db.scalar(select(m.Item))
    assert item
    plan_payload = s.FloorPlanIn(
        item_uuid=item.uuid,
    )

    res = client.post("/api/floor_plans/", content=plan_payload.model_dump_json(), headers=headers)

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


def test_delete_floor_plan(client: TestClient, full_db: Session, headers: dict[str, str]):
    # Delete a FloorPlan and verify the response
    item = full_db.scalar(select(m.Item))
    assert item

    plan_payload = s.FloorPlanIn(
        item_uuid=item.uuid,
    )

    res = client.post("/api/floor_plans/", content=plan_payload.model_dump_json(), headers=headers)

    plan_data = s.FloorPlanOut.model_validate(res.json())

    res = client.delete(f"/api/floor_plans/{plan_data.uuid}", headers=headers)
    assert res.status_code == 204

    deleted_plan = full_db.scalar(select(m.FloorPlan).where(m.FloorPlan.uuid == plan_data.uuid))
    assert deleted_plan and deleted_plan.is_deleted

    plan_res = client.get(f"/api/floor_plans/{item.uuid}", params={"store_url": item.store.url})

    plans = s.FloorPlanListOut.model_validate(plan_res.json())

    assert not plans.items
