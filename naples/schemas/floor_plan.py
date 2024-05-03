from pydantic import BaseModel, ConfigDict


class FloorPlanMarkerIn(BaseModel):
    x: float
    y: float
    floor_plan_uuid: str


class FloorPlanMarkerOut(BaseModel):
    uuid: str
    x: float
    y: float
    images: list[str]

    model_config = ConfigDict(
        from_attributes=True,
    )


class FloorPlanIn(BaseModel):
    item_uuid: str


class FloorPlanOut(BaseModel):
    uuid: str
    img_url: str
    markers: list[FloorPlanMarkerOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class FloorPlanListOut(BaseModel):
    items: list[FloorPlanOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
