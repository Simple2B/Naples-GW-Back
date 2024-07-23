import stripe
from fastapi import HTTPException, status

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
            amount=data.amount,
            currency=data.currency,
            recurring_interval=data.recurring_interval,
            stripe_product_id=res.stripe_product_id,
            stripe_price_id=res.stripe_price_id,
            is_deleted=data.is_deleted if data.is_deleted is not None else False,
            max_items=data.max_items,
            max_active_items=data.max_active_items,
            min_items=data.min_items,
            inactive_items=data.inactive_items,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        log(log.INFO, "Product [%s] with name [%s] created in db", product.uuid, data.type_name)

        return product

    return None


def get_product_by_id(product_price: str, db: Session) -> s.Product:
    """Get product by id"""

    product_db = db.scalar(sa.select(m.Product).where(m.Product.stripe_price_id == product_price))

    if not product_db:
        log(log.ERROR, "Product not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found, please contact support")

    return s.Product.model_validate(product_db)


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
        expand=["default_price"],  # type: ignore
        metadata={"max_active_items": data.max_active_items, "max_items": data.max_items},  # type: ignore
    )

    if (
        res
        and res.default_price is not None
        and (isinstance(res.default_price, stripe.Price) or isinstance(res.default_price, str))
    ):
        log(log.INFO, "Product [%s] with name [%s] created in stripe ", res.id, data.type_name)
        return s.StripeProductOut(
            stripe_product_id=res.id,
            stripe_price_id=res.default_price.id if isinstance(res.default_price, stripe.Price) else res.default_price,
        )

    else:
        log(log.ERROR, "Failed to get price ID from Stripe product")
        return None
