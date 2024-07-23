# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
# import sqlalchemy as sa

# from naples.config import config
# import naples.models as m

# from naples import schemas as s


# CFG = config("testing")


# def test_get_states(client: TestClient, full_db: Session, headers: dict[str, str]):
#     response = client.get("/api/locations/states", headers=headers)
#     assert response.status_code == 200
#     cities = s.LocationsListOut.model_validate(response.json())

#     assert cities.items


# def test_get_counties(client: TestClient, full_db: Session, headers: dict[str, str]):
#     state = full_db.scalar(sa.select(m.State))
#     assert state

#     response = client.get(f"/api/locations/counties/{state.uuid}", headers=headers)
#     assert response.status_code == 200
#     counties = s.LocationsListOut.model_validate(response.json())

#     assert counties.items


# def test_get_cities(client: TestClient, full_db: Session, headers: dict[str, str]):
#     county = full_db.scalar(sa.select(m.County))
#     assert county

#     response = client.get(f"/api/locations/cities/{county.uuid}", headers=headers)
#     assert response.status_code == 200
#     cities = s.LocationsListCityOut.model_validate(response.json())

#     assert cities.items
