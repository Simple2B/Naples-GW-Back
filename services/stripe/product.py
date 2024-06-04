import stripe

from sqlalchemy.orm import Session
import sqlalchemy as sa
from naples import schemas as s, models as m
from naples.config import config

from naples.logger import log

CFG = config()


def create_product(data: s.ProductIn, db: Session) -> s.ProductOut | None:
    stripe.api_key = CFG.STRIPE_SECRET_KEY

    products_db = db.scalars(sa.select(m.Product)).all()

    for product in products_db:
        if product.type_name == data.type_name:
            log(log.INFO, "Product [%s] already exists", product.type_name)
            return product

    # creat product in stripe
    res = stripe.Product.create(
        name=data.type_name,
        default_price_data={
            "unit_amount": data.amount * 100,
            "currency": data.currency,
            "recurring": {"interval": data.recurring_interval},
        },
        expand=["default_price"],
    )

    if res.default_price is not None and isinstance(res.default_price, stripe.Price):
        log(log.INFO, "Product [%s] with name [%s] created in stripe ", res.id, data.type_name)

        type_name = data.type_name.lower()

        product = m.Product(
            type_name=type_name,
            description=data.description,
            amount=data.amount,
            currency=data.currency,
            recurring_interval=data.recurring_interval,
            stripe_product_id=res.id,
            stripe_price_id=res.default_price.id,
            is_delete=data.is_delete if data.is_delete is not None else False,
        )

        db.add(product)
        db.flush()

        log(log.INFO, "Product [%s] with name [%s] created in db", product.uuid, data.type_name)

        if data.points:
            for point_text in data.points:
                point = m.Point(
                    text=point_text,
                    product_id=product.id,
                )
                db.add(point)
                db.flush()

        return product

    else:
        log(log.ERROR, "Failed to get price ID from Stripe product")
        return None
