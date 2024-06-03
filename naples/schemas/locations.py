from pydantic import BaseModel, ConfigDict


# cities schemas
class City(BaseModel):
    name: str
    county_uuid: str
    state_uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CityOut(City):
    uuid: str
    latitude: float
    longitude: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class Cities(BaseModel):
    cities: list[CityOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# counties schemas
class County(BaseModel):
    name: str
    state_id: int
    cities: list[CityOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class CountyIn(BaseModel):
    name: str
    state_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class CountyOut(County):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class Counties(BaseModel):
    counties: list[CountyOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# states schemas
class State(BaseModel):
    name: str
    abbreviated_name: str
    counties: list[CountyOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class StateIn(BaseModel):
    name: str
    abbreviated_name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class StateOut(State):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class States(BaseModel):
    states: list[StateOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationOut(BaseModel):
    name: str
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationCityOut(LocationOut):
    longitude: float
    latitude: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationsListOut(BaseModel):
    items: list[LocationOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class LocationsListCityOut(BaseModel):
    items: list[LocationCityOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
