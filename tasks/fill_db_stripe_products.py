import sys
from invoke import task


sys.path = ["", ".."] + sys.path[1:]

from services.stripe.product import create_product  # noqa: E402


@task
def fill_db_stripe_products(with_print: bool = True):
    """Fill db with stripe products"""

    from naples.database import db
    from naples import schemas as s

    with db.begin() as session:
        stripe_products: list[s.ProductIn] = [
            s.ProductIn(
                type_name="starter",
                description="1-3 Properties",
                amount=14,
                currency="usd",
                recurring_interval="month",
                points=["Up to 3 active", "2 Unactive"],
            ),
            s.ProductIn(
                type_name="plus",
                description="4-10 Properties",
                amount=29,
                currency="usd",
                recurring_interval="month",
                points=["Up to 10 active", "5 Unactive"],
            ),
            s.ProductIn(
                type_name="pro",
                description="11-30 Properties",
                amount=49,
                currency="usd",
                recurring_interval="month",
                points=["Up to 30 active", "10 Unactive"],
            ),
        ]

        for product in stripe_products:
            create_product(data=product, db=session)
