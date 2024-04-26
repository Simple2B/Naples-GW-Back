import sys
from invoke import task
from pathlib import Path


sys.path = ["", ".."] + sys.path[1:]

from naples.models import db  # noqa: E402
from services.export_usa_locations import export_usa_locations_from_csv_file  # noqa: E402

MODULE_PATH = Path(__file__).parent
CSV_FILE = MODULE_PATH / ".." / "data" / "uscities.csv"


# this task is for filling db with New York locations for staging
@task
def fill_db_newyork_locations(with_print: bool = True):
    """Export New York locations from csv file to db"""
    with db.begin() as session:
        export_usa_locations_from_csv_file(session, CSV_FILE, is_new_york=True)
