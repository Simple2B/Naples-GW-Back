import sys
from invoke import task
from pathlib import Path


sys.path = ["", ".."] + sys.path[1:]

from naples.models import db  # noqa: E402
from services.export_usa_locations import export_usa_locations_from_csv_file  # noqa: E402

MODULE_PATH = Path(__file__).parent
CSV_FILE = MODULE_PATH / ".." / "data" / "uscities.csv"


@task
def fill_db_locations(with_print: bool = True):
    """Export USA locations from csv file to db"""
    with db.begin() as session:
        export_usa_locations_from_csv_file(session, CSV_FILE)
