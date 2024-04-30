import sys
from typing import Sequence
from invoke import task
from pathlib import Path


sys.path = ["", ".."] + sys.path[1:]

from naples.models import db  # noqa: E402
from naples import schemas as s  # noqa: E402
from naples.logger import log  # noqa: E402
from services.export_usa_locations import export_usa_locations_from_csv_file  # noqa: E402


MODULE_PATH = Path(__file__).parent
CSV_FILE = MODULE_PATH / ".." / "data" / "uscities.csv"


# this task is for filling db with New York locations for staging
def fill_db_newyork_locations(with_print: bool = True):
    """Export New York locations from csv file to db"""
    with db.begin() as session:
        export_usa_locations_from_csv_file(session, CSV_FILE, is_new_york=True)


# create user, store, member (realtor in item) and items for staging
def create_user_with_store():
    """Create user, store, member (realtor in item) and items for staging"""

    from naples import models as m
    from naples.database import db
    from services.create_test_data import create_item, create_member, create_store, create_user

    file = open("data/test_data.json")
    test_data = s.TestData.model_validate_json(file.read())

    with db.begin() as session:
        for user in test_data.test_users:
            new_user: m.User = session.query(m.User).filter(m.User.email == user.email).first()
            if not new_user:
                new_user = create_user(user)
                session.add(new_user)
                log(log.INFO, "User [%s] created", new_user.email)
                session.flush()

        test_store_data = test_data.test_stores[0]
        test_store: m.Store = m.Store(**test_store_data.model_dump())
        store = session.query(m.Store).filter(m.Store.uuid == test_store.uuid).first()
        if not store:
            store = create_store(test_store)
            session.add(store)
            log(log.INFO, "Store [%s] created", test_store.name)
            session.flush()

        test_members_data = test_data.test_members
        test_members: list[m.Member] = [m.Member(**member.model_dump()) for member in test_members_data]

        for member in test_members:
            member_db: m.Member = session.query(m.Member).filter(m.Member.uuid == member.uuid).first()
            if not member_db:
                new_member = create_member(member)
                session.add(new_member)
                log(log.INFO, "Member [%s] created", member.name)
                session.flush()

        test_items_data = test_data.test_items
        test_items: list[m.Item] = [m.Item(**item.model_dump()) for item in test_items_data]
        cities: Sequence[m.City] = session.query(m.City).all()
        cities_ids = [city.id for city in cities]
        for test_item in test_items:
            item_db = session.query(m.Item).filter(m.Item.uuid == test_item.uuid).first()
            if not item_db:
                index = test_items.index(test_item)
                city_id = cities_ids[index % len(cities_ids)]
                item = create_item(test_item, city_id)
                log(log.INFO, "Item [%s] created with city [%s]", test_item.name, city_id)
                session.add(item)

    session.commit()


@task
def fill_db_staging_data(with_print: bool = True):
    fill_db_newyork_locations(with_print)
    create_user_with_store()
