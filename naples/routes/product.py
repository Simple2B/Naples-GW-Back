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

    products_db = db.scalars(sa.select(m.Product).where(~m.Product.is_delete)).all()

    log(log.INFO, "User [%s] get products [%s] prices", current_user.email, len(products_db))

    return s.ProductsOut(
        products=[
            s.ProductOut(
                uuid=product.uuid,
                type_name=product.type_name,
                description=product.description,
                amount=product.amount,
                points=product.points,
                is_delete=product.is_delete,
                stripe_product_id=product.stripe_product_id,
                stripe_price_id=product.stripe_price_id,
                created_at=product.created_at,
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

    product: s.ProductOut | None = create_product(data, db)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get price ID from Stripe product"
        )

    log(log.INFO, "User [%s] created product [%s]", current_user.email, product.uuid)

    return product
