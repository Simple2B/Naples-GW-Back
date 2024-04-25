from typing import Sequence
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.config import config
import naples.models as m

from .test_data import TestData

CFG = config("testing")


def test_get_locations(client: TestClient, full_db: Session, headers: dict[str, str], test_data: TestData):
    db = full_db
    states: Sequence[m.State] = db.scalars(sa.select(m.State)).all()
    assert states[0].name == "New York"
    response = client.get("/api/locations/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get("states")) == len(states)
