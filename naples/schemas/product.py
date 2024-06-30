from datetime import datetime
import enum

from pydantic import BaseModel, ConfigDict
from naples.config import config


CFG = config()


class ProductType(enum.Enum):
    STARTER = "starter"
    PLUS = "plus"
    PRO = "pro"


class ProductTypeRecurringInterval(enum.Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Product(BaseModel):
    type_name: str
    amount: int
    is_deleted: bool

    stripe_product_id: str
    stripe_price_id: str

    created_at: datetime

    max_items: int
    max_active_items: int
    min_items: int
    inactive_items: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductIn(BaseModel):
    type_name: str = ProductType.STARTER.value
    amount: int
    is_deleted: bool | None = None
    max_items: int
    max_active_items: int

    min_items: int
    inactive_items: int

    currency: str = "usd"
    recurring_interval: str = ProductTypeRecurringInterval.MONTH.value

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


class StripeProductOut(BaseModel):
    stripe_product_id: str
    stripe_price_id: str


class ProductBase(BaseModel):
    type_name: str
    amount: int
    is_deleted: bool

    created_at: datetime

    max_items: int
    max_active_items: int

    min_items: int
    inactive_items: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductBaseOut(ProductBase):
    uuid: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductsBaseOut(BaseModel):
    products: list[ProductBaseOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# class ProductsDictBaseOut(BaseModel):
#     class ProductModel(RootModel[Dict[str, ProductBaseOut]]):
#         def __getattr__(self, item: str):
#             return self.root.__getitem__(item)

#     products: ProductModel


class ProductModify(BaseModel):
    stripe_price_id: str
    amount: int | None = None

    max_items: int | None = None
    max_active_items: int | None = None

    min_items: int | None = None
    inactive_items: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
