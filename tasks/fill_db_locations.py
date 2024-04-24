import sys
import csv
from pathlib import Path
from invoke import task

from typing import List


import sqlalchemy as sa

sys.path = ["", ".."] + sys.path[1:]

from naples import models as m  # noqa: E402
from naples.models import db  # noqa: E402
from naples import schemas as s  # noqa: E402
from naples.logger import log  # noqa: E402


MODULE_PATH = Path(__file__).parent
CSV_FILE = MODULE_PATH / ".." / "data" / "uscities.csv"


def check_if_state_exists(state: str, session: sa.orm.Session) -> bool:
    """Check if state exists in db"""
    stmt = sa.select(m.State).where(m.State.name == state)
    db_state = session.scalar(stmt)
    return bool(db_state)


def check_if_county_exists(county: str, state_id: int, session: sa.orm.Session) -> bool:
    """Check if county exists in db"""
    stmt = sa.select(m.County).where(m.County.name == county, m.County.state_id == state_id)
    db_county = session.scalar(stmt)
    return bool(db_county)


def check_if_city_exists(city: str, county_id: int, session: sa.orm.Session) -> bool:
    """Check if city exists in db"""
    stmt = sa.select(m.City).where(m.City.name == city, m.City.county_id == county_id)
    db_city = session.scalar(stmt)
    return bool(db_city)


@task
def export_usa_locations_from_csv_file(with_print: bool = True):
    """Export USA locations from csv file to db"""

    with open(CSV_FILE, "r") as file:
        csvreader = csv.reader(file)
        header = next(csvreader)

        log(log.INFO, "Header: %s", header)
        # all colums
        # ['city', 'city_ascii', 'state_id', 'state_name', 'county_fips', 'county_name', 'lat', 'lng', 'population', 'density', 'source', 'incorporated', 'timezone', 'zips', 'id']

        # colums what we need for db
        # ['city', 'city_ascii', 'state_id', 'state_name', 'county_name']

        CITY_NAME_INDEX = header.index("city")

        # TODO: check if we need this field (it seams this field the same as city)
        # ASCII (American Standard Code for Information Interchange)
        # CITY_ASCII_INDEX = header.index("city_ascii")

        ABBREVIATED_NAME_INDEX = header.index("state_id")
        STATE_NAME_INDEX = header.index("state_name")
        COUNTY_NAME_INDEX = header.index("county_name")

        rows: List[List[str]] = []
        for row in csvreader:
            rows.append(row)
        log(log.INFO, "Rows count: %s", len(rows))

        file.close()

    with db.begin() as session:
        for row in rows:
            state_name = row[STATE_NAME_INDEX]
            abbreviated_name = row[ABBREVIATED_NAME_INDEX]
            if check_if_state_exists(state_name, session):
                log(log.INFO, "State [%s] already exists", state_name)
                continue

            state_db = m.State(
                name=state_name,
                abbreviated_name=abbreviated_name,
            )
            session.add(state_db)
            session.flush()

            county_name = row[COUNTY_NAME_INDEX]

            if check_if_county_exists(county_name, state_db.id, session):
                log(log.INFO, "County [%s] already exists", county_name)
                continue

            county_db = m.County(
                name=county_name,
                state_id=state_db.id,
            )
            session.add(county_db)
            session.flush()

            city_name = row[CITY_NAME_INDEX]

            if check_if_city_exists(city_name, county_db.id, session):
                log(log.INFO, "City [%s] already exists", row[CITY_NAME_INDEX])
                continue

            city_db = m.City(
                name=city_name,
                county_id=county_db.id,
            )
            session.add(city_db)
            session.flush()

    print("[Done]: Export USA locations from csv file to db")
    return
