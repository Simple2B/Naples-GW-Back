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
        max_items=2,
        max_active_items=3,
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
