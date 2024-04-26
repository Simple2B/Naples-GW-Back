from typing import Sequence, cast
from fastapi import Depends, APIRouter, status, HTTPException

import naples.models as m
import naples.schemas as s
from naples.logger import log

import sqlalchemy as sa
from sqlalchemy.orm import Session
# from sqlalchemy.sql.expression import Executable

from naples.dependency import get_current_user
from naples.database import get_db


location_router = APIRouter(prefix="/locations", tags=["Location - State/County/City"])


@location_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.States,
    responses={
        404: {"description": "States not found"},
    },
)
def get_locations(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get all locations (states/counties/cities)"""

    query = sa.select(m.State)
    states: Sequence[m.State] = db.scalars(query).all()

    if not states:
        log(log.ERROR, "States [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="States not found")

    return s.States(states=cast(list, states))
