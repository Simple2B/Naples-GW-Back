from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa


from naples import schemas as s, models as m
from naples.config import config


CFG = config("testing")


def test_create_stripe_product_get_products(
    client: TestClient,
    admin_headers: dict[str, str],
    full_db: Session,
):
    test_stripe_product = s.ProductIn(
        type_name="test product",
        amount=1,
        currency="usd",
        recurring_interval=s.ProductTypeRecurringInterval.MONTH.value,
        max_items=5,
        max_active_items=3,
        min_items=11,
        inactive_items=30,
    )

    res = client.post(
        "/api/products/",
        headers=admin_headers,
        json=test_stripe_product.model_dump(),
    )

    assert res.status_code == 200

    response = client.get(
        "/api/products/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    db_product = full_db.scalar(sa.select(m.Product).where(m.Product.type_name == test_stripe_product.type_name))

    assert db_product is not None
    assert db_product.type_name in response.text

    response = client.get("/api/products/base")

    assert response.status_code == 200

    update_data = s.ProductModify(
        stripe_price_id=db_product.stripe_price_id,
        max_items=10,
        max_active_items=5,
        min_items=3,
        inactive_items=7,
    )

    # update product
    res = client.patch(
        "/api/products/",
        headers=admin_headers,
        json=update_data.model_dump(),
    )

    response.status_code == 200
