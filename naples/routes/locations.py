from typing import Sequence
from fastapi import Depends, APIRouter, status, HTTPException

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
# from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user
from naples.database import get_db


location_router = APIRouter(
    prefix="/locations", tags=["Location - State/County/City"], dependencies=[Depends(get_current_user)]
)


@location_router.get(
    "/states",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsListOut,
    responses={
        404: {"description": "States not found"},
    },
)
def get_locations(
    db: Session = Depends(get_db),
):
    """Get all locations (states/counties/cities)"""

    log(log.INFO, "Getting all states")

    states: Sequence[m.State] = db.scalars(sa.select(m.State)).all()

    if not states:
        log(log.ERROR, "States [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="States not found")

    return s.LocationsListOut(items=list(states))


@location_router.get(
    "/counties/{state_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsListOut,
    responses={
        404: {"description": "State not found"},
    },
)
def get_counties_for_state(
    state_uuid: str,
    db: Session = Depends(get_db),
):
    log(log.INFO, "Getting all counties for state")

    counties = db.scalars(sa.select(m.County).where(m.County.state.has(m.State.uuid == state_uuid))).all()

    if not counties:
        log(log.ERROR, "Counties [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counties not found")

    return s.LocationsListOut(items=list(counties))


@location_router.get(
    "/cities/{county_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.LocationsListOut,
    responses={
        404: {"description": "County not found"},
    },
)
def get_cities_for_county(
    county_uuid: str,
    db: Session = Depends(get_db),
):
    log(log.INFO, "Getting all cities for county")

    cities = db.scalars(sa.select(m.City).where(m.City.county.has(m.County.uuid == county_uuid))).all()

    if not cities:
        log(log.ERROR, "Cities [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cities not found")

    return s.LocationsListOut(items=list(cities))
