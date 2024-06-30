import sys
from invoke import task


sys.path = ["", ".."] + sys.path[1:]

from services.stripe.product import create_product  # noqa: E402


@task
def fill_db_stripe_products(with_print: bool = True):
    """Fill db with stripe products"""

    from naples.database import db
    from naples import schemas as s

    with db.Session() as session:
        stripe_products: list[s.ProductIn] = [
            s.ProductIn(
                type_name=s.ProductType.STARTER.value,
                amount=14,
                currency="usd",
                recurring_interval=s.ProductTypeRecurringInterval.MONTH.value,
                # points=["Up to 3 active", "2 Unactive"],
                max_items=6,
                max_active_items=3,
                min_items=1,
                inactive_items=3,
            ),
            s.ProductIn(
                type_name=s.ProductType.PLUS.value,
                amount=29,
                currency="usd",
                recurring_interval=s.ProductTypeRecurringInterval.MONTH.value,
                # points=["Up to 10 active", "5 Unactive"],
                max_items=20,
                max_active_items=10,
                min_items=4,
                inactive_items=10,
            ),
            s.ProductIn(
                type_name=s.ProductType.PRO.value,
                amount=59,
                currency="usd",
                recurring_interval=s.ProductTypeRecurringInterval.MONTH.value,
                # points=["Up to 30 active", "10 Unactive"],
                max_items=60,
                max_active_items=30,
                min_items=11,
                inactive_items=30,
            ),
        ]

        for product in stripe_products:
            create_product(data=product, db=session)


@task
def fill_db_stripe_test_products(with_print: bool = True):
    """Fill db with stripe test products"""

    from naples.database import db
    from naples import schemas as s

    with db.Session() as session:
        stripe_products: list[s.ProductIn] = [
            s.ProductIn(
                type_name="test product",
                amount=14,
                currency="usd",
                recurring_interval=s.ProductTypeRecurringInterval.MONTH.value,
                # points=["Up to 3 active", "2 Unactive"],
                max_items=6,
                max_active_items=3,
                min_items=1,
                inactive_items=3,
            ),
        ]

        for product in stripe_products:
            create_product(data=product, db=session)
