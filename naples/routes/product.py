from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
from naples.dependency.user import get_current_user
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

    return s.ProductsOut(
        products=[
            s.ProductOut(
                uuid=product.uuid,
                type_name=product.type_name,
                description=product.description,
                amount=product.amount,
                points=product.points,
                is_deleted=product.is_deleted,
                stripe_product_id=product.stripe_product_id,
                stripe_price_id=product.stripe_price_id,
                created_at=product.created_at,
            )
            for product in products_db
        ]
    )


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

    return s.ProductsBaseOut(
        products=[
            s.ProductBaseOut(
                uuid=product.uuid,
                type_name=product.type_name,
                description=product.description,
                amount=product.amount,
                is_deleted=product.is_deleted,
                created_at=product.created_at,
                points=product.points,
            )
            for product in products_db
        ]
    )


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
):
    """Create a product"""

    # TODO: for admin users (add MAX_COUNT_PRODUCTS)
    # query = db.scalar(sa.select(m.Product))

    # if query:
    #     products = query.all()

    #     if len(products) > CFG.MAX_COUNT_PRODUCTS:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST, detail=f"Max count of products is {CFG.MAX_COUNT_PRODUCTS}"
    #         )

    product: s.ProductOut | None = create_product(data, db)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get price ID from Stripe product"
        )

    log(log.INFO, "User [%s] created product [%s]", current_user.email, product.uuid)

    return product
