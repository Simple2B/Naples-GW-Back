from fastapi.testclient import TestClient


from naples import schemas as s

# import naples.models as m
from naples.config import config


CFG = config("testing")


def test_create_checkout_session(
    client: TestClient,
    headers: dict[str, str],
    test_data: s.TestData,
    stripe_checkout_session: s.CheckoutSessionOut,
):
    data = s.SubscriptionIn(
        product_price_id=CFG.STRIPE_PRICE_STARTER_ID,
    )
    response = client.post("/api/billings/create-checkout-session", json=data.model_dump(), headers=headers)
    assert response.status_code

    response_data = s.CheckoutSessionOut.model_validate_json(response.text)
    assert response_data
    assert response_data.id
    assert response_data.url
