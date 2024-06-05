from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa


from naples import schemas as s, models as m
from naples.config import config


CFG = config("testing")


def test_create_stripe_product_get_products(
    client: TestClient, headers: dict[str, str], test_data: s.TestData, full_db: Session
):
    test_stripe_product = s.ProductIn(
        type_name="test product",
        description="description",
        amount=1,
        currency="usd",
        recurring_interval="month",
        points=["point 1", "point 2"],
    )

    res = client.post(
        "/api/products/",
        headers=headers,
        json=test_stripe_product.model_dump(),
    )

    assert res.status_code == 200

    response = client.get(
        "/api/products/",
        headers=headers,
    )

    assert response.status_code == 200

    db_product = full_db.scalar(sa.select(m.Product).where(m.Product.type_name == test_stripe_product.type_name))

    assert db_product is not None
    assert db_product.type_name in response.text
