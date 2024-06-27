from pydantic import BaseModel, ConfigDict


class Metadata(BaseModel):
    key: str
    value: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Metadaties(BaseModel):
    metadaties: list[Metadata]

    model_config = ConfigDict(
        from_attributes=True,
    )
