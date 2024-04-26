from pydantic import BaseModel, ConfigDict


# cities schemas
class City(BaseModel):
    name: str
    county_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class CityOut(City):
    uuid: str

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
    cities: list[City] = []

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
    counties: list[County] = []

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
