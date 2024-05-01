from pydantic import BaseModel


class FlorPlanMarkerIn(BaseModel):
    x: float
    y: float
    floor_plan_uuid: str
    image_uuids: list[str]


class FloorPlanMarkerOut(BaseModel):
    uuid: str
    x: float
    y: float
    images: list[str]


class FloorPlanIn(BaseModel):
    img_uuid: str
    item_uuid: str


class FloorPlanOut(BaseModel):
    uuid: str
    img_url: str
    markers: list[FloorPlanMarkerOut]
