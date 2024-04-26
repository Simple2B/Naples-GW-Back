import sys
import csv
from pathlib import Path

from typing import List, Sequence, cast

from sqlalchemy.orm import Session
import sqlalchemy as sa

sys.path = ["", ".."] + sys.path[1:]

from naples import models as m  # noqa: E402

from naples import schemas as s  # noqa: E402
from naples.logger import log  # noqa: E402

NEW_YORK = "NY"


def get_data_from_csv_file(file_path: Path):
    with open(file_path, "r") as file:
        csvreader = csv.reader(file)
        header = next(csvreader)

        log(log.INFO, "Header: %s", header)
        # all colums
        # ['city', 'city_ascii', 'state_id', 'state_name', 'county_fips', 'county_name', 'lat', 'lng', 'population', 'density', 'source', 'incorporated', 'timezone', 'zips', 'id']

        # colums what we need for db
        # ['city', 'state_id', 'state_name', 'county_name']

        CITY_NAME_INDEX = header.index("city")
        ABBREVIATED_NAME_INDEX = header.index("state_id")
        STATE_NAME_INDEX = header.index("state_name")
        COUNTY_NAME_INDEX = header.index("county_name")

        rows: List[List[str]] = []
        for row in csvreader:
            rows.append(row)
        log(log.INFO, "Rows count: %s", len(rows))

        file.close()

        return rows, CITY_NAME_INDEX, ABBREVIATED_NAME_INDEX, STATE_NAME_INDEX, COUNTY_NAME_INDEX


def export_usa_locations_from_csv_file(session: Session, file_path: Path, is_new_york: bool = False):
    """Export USA locations from csv file to db"""

    rows, CITY_NAME_INDEX, ABBREVIATED_NAME_INDEX, STATE_NAME_INDEX, COUNTY_NAME_INDEX = get_data_from_csv_file(
        file_path
    )

    for row in rows:
        state_name = row[STATE_NAME_INDEX]
        abbreviated_name = row[ABBREVIATED_NAME_INDEX]
        county_name = row[COUNTY_NAME_INDEX]

        if is_new_york and abbreviated_name != NEW_YORK:
            continue

        state_db: m.State | None = session.scalar(
            sa.select(m.State).where(m.State.abbreviated_name == abbreviated_name)
        )

        if not state_db:
            state_db = m.State(
                name=state_name,
                abbreviated_name=abbreviated_name,
            )

            session.add(state_db)
            session.flush()
            log(log.INFO, "New state [%s] created", abbreviated_name)

        county_db: m.County | None = session.scalar(
            sa.select(m.County).where(m.County.name == county_name, m.County.state_id == state_db.id)
        )

        if not county_db:
            county_db = m.County(
                name=county_name,
                state_id=state_db.id,
            )
            session.add(county_db)
            session.flush()

            log(log.INFO, "County [%s] created for state [%s]", county_name, abbreviated_name)

        city_name = row[CITY_NAME_INDEX]

        city_db: m.City | None = session.scalar(
            sa.select(m.City).where(m.City.name == city_name, m.City.county_id == county_db.id)
        )

        if not city_db:
            city_db = m.City(
                name=city_name,
                county_id=county_db.id,
            )

            session.add(city_db)
            session.flush()

            log(log.INFO, "City [%s] created for county [%s]", city_name, county_name)

    log(log.INFO, "[Done]: Export USA locations from csv file to db")

    query = sa.select(m.State)
    states: Sequence[m.State] = session.scalars(query).all()
    return s.States(states=cast(list, states))
