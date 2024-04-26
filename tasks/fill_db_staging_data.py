import sys
import json
from invoke import task
from pathlib import Path


sys.path = ["", ".."] + sys.path[1:]

from naples.models import db  # noqa: E402
from naples.logger import log  # noqa: E402
from services.export_usa_locations import export_usa_locations_from_csv_file  # noqa: E402


MODULE_PATH = Path(__file__).parent
CSV_FILE = MODULE_PATH / ".." / "data" / "uscities.csv"


# this task is for filling db with New York locations for staging
def fill_db_newyork_locations(with_print: bool = True):
    """Export New York locations from csv file to db"""
    with db.begin() as session:
        export_usa_locations_from_csv_file(session, CSV_FILE, is_new_york=True)


# create user, store, member (rieltor in item) and items for staging
def create_user_with_store():
    """Create user, store, member (rieltor in item) and items for staging"""

    from naples import models as m
    from naples.database import db

    file = open("data/test_data.json")
    test_data = json.load(file)

    with db.begin() as session:
        test_user: m.User = test_data["test_users"][0]

        user: m.User = session.query(m.User).filter(m.User.email == test_user["email"]).first()
        if not user:
            user = m.User(
                id=test_user["id"],
                email=test_user["email"],
                password=test_user["password"],
            )
            session.add(user)
            log(log.INFO, "User [%s] created", test_user["email"])
            session.flush()

        test_store: m.Store = test_data["test_stores"][0]
        store = session.query(m.Store).filter(m.Store.uuid == test_store["uuid"]).first()
        if not store:
            store = m.Store(
                uuid=test_store["uuid"],
                name=test_store["name"],
                header=test_store["header"],
                sub_header=test_store["sub_header"],
                url=test_store["url"],
                logo_url=test_store["logo_url"],
                about_us=test_store["about_us"],
                email=test_store["email"],
                phone=test_store["phone"],
                instagram_url=test_store["instagram_url"],
                messenger_url=test_store["messenger_url"],
                user_id=test_store["user_id"],
            )
            session.add(store)
            log(log.INFO, "Store [%s] created", test_store["name"])
            session.flush()

        test_members: list[m.Member] = test_data["test_members"]
        for member in test_members:
            member_db: m.Member = session.query(m.Member).filter(m.Member.uuid == member["uuid"]).first()
            if not member_db:
                new_member = m.Member(
                    uuid=member["uuid"],
                    name=member["name"],
                    email=member["email"],
                    phone=member["phone"],
                    instagram_url=member["instagram_url"],
                    messenger_url=member["messenger_url"],
                    avatar_url=member["avatar_url"],
                    store_id=member["store_id"],
                )
                session.add(new_member)
                log(log.INFO, "Member [%s] created", member["name"])
                session.flush()

        test_items: list[m.Item] = test_data["test_items"]
        for test_item in test_items:
            item_db = session.query(m.Item).filter(m.Item.uuid == test_item["uuid"]).first()
            if not item_db:
                item = m.Item(
                    uuid=test_item["uuid"],
                    name=test_item["name"],
                    description=test_item["description"],
                    latitude=test_item["latitude"],
                    longitude=test_item["longitude"],
                    address=test_item["address"],
                    size=test_item["size"],
                    bedrooms_count=test_item["bedrooms_count"],
                    bathrooms_count=test_item["bathrooms_count"],
                    stage=test_item["stage"],
                    category=test_item["category"],
                    type=test_item["type"],
                    store_id=test_item["store_id"],
                    realtor_id=test_item["realtor_id"],
                )
                log(log.INFO, "Item [%s] created", test_item["name"])
                session.add(item)

    session.commit()


@task
def fill_db_staging_data(with_print: bool = True):
    fill_db_newyork_locations(with_print)
    create_user_with_store()
