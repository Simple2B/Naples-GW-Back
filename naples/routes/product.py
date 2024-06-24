from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.database import get_db
from naples.dependency import get_current_user, get_admin
from naples import schemas as s, models as m
from naples.config import config
from naples.logger import log
from naples.routes.utils import get_base_product_data, get_product_data
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

    return s.ProductsOut(products=[get_product_data(product) for product in products_db])


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

    return s.ProductsBaseOut(products=[get_base_product_data(product) for product in products_db])


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
    query = db.scalar(sa.select(m.Product))

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
