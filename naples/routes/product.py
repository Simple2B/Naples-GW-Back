from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa
import stripe

from naples.database import get_db
from naples.dependency import get_current_user, get_admin
from naples import schemas as s, models as m
from naples.config import config
from naples.logger import log
from services.stripe.product import create_product


product_router = APIRouter(prefix="/products", tags=["Products"])

CFG = config()


@product_router.get(
    "/",
    response_model=s.ProductsOut,
    status_code=status.HTTP_200_OK,
)
def get_products(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get products"""

    products_db = db.scalars(sa.select(m.Product).where(~m.Product.is_deleted)).all()

    log(log.INFO, "User [%s] get products [%s] prices", current_user.email, len(products_db))

    products = dict()

    for product in products_db:
        if product.type_name == s.ProductType.STARTER.value:
            products.update({"starter": s.ProductOut.model_validate(product)})
        if product.type_name == s.ProductType.PLUS.value:
            products.update({"plus": s.ProductOut.model_validate(product)})
        if product.type_name == s.ProductType.PRO.value:
            products.update({"pro": s.ProductOut.model_validate(product)})

    return s.ProductsOut.model_validate(products)


@product_router.get(
    "/base",
    response_model=s.ProductsBaseOut,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No products found"},
    },
)
def get_base_products(
    db: Session = Depends(get_db),
):
    """Get base products"""

    products_db = db.scalars(sa.select(m.Product).where(~m.Product.is_deleted)).all()

    if not products_db:
        log(log.INFO, "No products found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found")

    products = dict()

    for product in products_db:
        if product.type_name == s.ProductType.STARTER.value:
            products.update({"starter": s.ProductBaseOut.model_validate(product)})
        if product.type_name == s.ProductType.PLUS.value:
            products.update({"plus": s.ProductBaseOut.model_validate(product)})
        if product.type_name == s.ProductType.PRO.value:
            products.update({"pro": s.ProductBaseOut.model_validate(product)})

    return s.ProductsBaseOut.model_validate(products)


# for admin panel
# TODO:  for admin users
@product_router.post(
    "/",
    response_model=s.ProductOut,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Failed to get price ID from Stripe product"},
    },
)
def create_stripe_product(
    data: s.ProductIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Create a product"""

    # TODO: for admin users
    query = db.scalars(sa.select(m.Product))

    if query:
        products = query.all()

        if len(products) > CFG.MAX_PRODUCTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Max count of products is {CFG.MAX_PRODUCTS}"
            )

    product: s.ProductOut | None = create_product(data, db)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get price ID from Stripe product"
        )

    log(log.INFO, "User [%s] created product [%s]", current_user.email, product.uuid)

    return product


# for admin panel
@product_router.patch(
    "/product",
    status_code=status.HTTP_200_OK,
    response_model=s.Product,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
    },
)
def update_product(
    data: s.ProductModify,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
    admin: m.User = Depends(get_admin),
):
    """Update product"""

    product_db: m.Product | None = db.scalar(
        sa.select(m.Product).where(m.Product.stripe_price_id == data.stripe_price_id)
    )

    if not product_db:
        log(log.INFO, "Product not found in db")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if data.amount:
        # create new price on stripe and add as defaulte price to stripe product
        # update product in db with new stripe price id and amount

        # modify product default price in stripe
        try:
            product_stripe_response = stripe.Product.retrieve(product_db.stripe_product_id)

            log(log.INFO, "Product [%s] retrieved from stripe", product_stripe_response.name)

            # get list of prices for product
            prices = stripe.Price.list(active=True, product=product_db.stripe_product_id)

            # get amouts and price id of prices
            prices_data = {price.unit_amount: price.id for price in prices}

            price_response_id = ""

            # check if such amont already exists
            if data.amount * 100 in prices_data:
                price_response_id = prices_data[data.amount * 100]
                log(log.INFO, "Price for product [%s] already exists", product_db.type_name)
            else:
                price_response = stripe.Price.create(
                    currency="usd",
                    unit_amount=data.amount * 100,
                    recurring={"interval": product_db.recurring_interval},  # type: ignore
                    product=product_db.stripe_product_id,
                )
                price_response_id = price_response.id

                log(log.INFO, "Product [%s] modified in stripe with new price", product_db.type_name)

            product_response = stripe.Product.modify(
                product_db.stripe_product_id,
                default_price=price_response_id,
            )

            log(log.INFO, "Product [%s] modified in stripe with new default price", product_response.name)

            product_db.amount = data.amount
            product_db.stripe_price_id = price_response_id

            log(log.INFO, "Product [%s] modified in db with new price", product_db.type_name)

        except stripe.StripeError as e:
            log(log.ERROR, "Failed to modify product in stripe [%s]", e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to modify product in stripe")

    if data.min_items:
        product_db.min_items = data.min_items
        log(log.INFO, "Product [%s] modified in db with new min items", product_db.type_name)

    if data.max_items:
        product_db.max_items = data.max_items
        log(log.INFO, "Product [%s] modified in db with new max items", product_db.type_name)

    if data.max_active_items:
        product_db.max_active_items = data.max_active_items
        log(log.INFO, "Product [%s] modified in db with new max active items", product_db.type_name)

    if data.inactive_items:
        product_db.inactive_items = data.inactive_items
        log(log.INFO, "Product [%s] modified in db with new unactive items", product_db.type_name)

    db.commit()
    db.refresh(product_db)
    log(log.INFO, "Product [%s] modified in db", product_db.type_name)

    return s.Product.model_validate(product_db)
