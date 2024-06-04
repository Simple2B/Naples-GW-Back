from datetime import datetime

from pydantic import BaseModel, ConfigDict
from naples.config import config


CFG = config()


class Product(BaseModel):
    type_name: str
    description: str
    amount: int
    is_delete: bool

    stripe_product_id: str = ""
    stripe_price_id: str = ""

    created_at: datetime
    points: list

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductIn(BaseModel):
    type_name: str
    description: str
    amount: int
    is_delete: bool | None = None
    points: list[str] | None = None
    currency: str = "usd"
    recurring_interval: str = "month"

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductOut(Product):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductsOut(BaseModel):
    products: list[ProductOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
