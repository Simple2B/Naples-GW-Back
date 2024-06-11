import stripe

from sqlalchemy.orm import Session
import sqlalchemy as sa
from naples import schemas as s, models as m
from naples.config import config

from naples.logger import log

CFG = config()


def create_product(data: s.ProductIn, db: Session) -> s.ProductOut | None:
    stripe.api_key = CFG.STRIPE_SECRET_KEY

    product: s.ProductOut | None = db.scalars(sa.select(m.Product).where(m.Product.type_name == data.type_name)).first()

    if product:
        log(log.INFO, "Product [%s] already exists", data.type_name)
        return product

    res: s.StripeProductOut | None = get_stripe_product(data)

    if res:
        type_name = data.type_name.lower()

        product = m.Product(
            type_name=type_name,
            description=data.description,
            amount=data.amount,
            currency=data.currency,
            recurring_interval=data.recurring_interval,
            stripe_product_id=res.stripe_product_id,
            stripe_price_id=res.stripe_price_id,
            is_deleted=data.is_deleted if data.is_deleted is not None else False,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        log(log.INFO, "Product [%s] with name [%s] created in db", product.uuid, data.type_name)

        if data.points:
            for point_text in data.points:
                point = m.Point(
                    text=point_text,
                    product_id=product.id,
                )
                db.add(point)
                db.commit()
                db.refresh(product)

        return product

    return None


def get_stripe_product(data: s.ProductIn) -> s.StripeProductOut | None:
    stripes_products = stripe.Product.list(active=True)

    log(log.INFO, "Stripe products: [%s]", len(stripes_products.data))

    if stripes_products.data:
        products = [product for product in stripes_products if product.name == data.type_name]

        if products and products[0].default_price is not None and isinstance(products[0].default_price, str):
            return s.StripeProductOut(
                stripe_product_id=products[0].id,
                stripe_price_id=products[0].default_price,
            )

    res = stripe.Product.create(
        name=data.type_name,
        default_price_data={
            "unit_amount": data.amount * 100,
            "currency": data.currency,
            "recurring": {"interval": data.recurring_interval},  # type: ignore
        },
        expand=["default_price"],
        metadata={"description": data.description},
    )

    if res and res.default_price is not None and isinstance(res.default_price, stripe.Price):
        log(log.INFO, "Product [%s] with name [%s] created in stripe ", res.id, data.type_name)
        return s.StripeProductOut(
            stripe_product_id=res.id,
            stripe_price_id=res.default_price.id,
        )

    else:
        log(log.ERROR, "Failed to get price ID from Stripe product")
        return None
