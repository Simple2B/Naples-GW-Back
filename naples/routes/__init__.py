# ruff: noqa: F401
import stripe

from fastapi import APIRouter, Request

from naples.config import config

from .user import user_router

from .auth import router as auth_router
from .store import store_router
from .locations import location_router
from .item import item_router
from .member import member_router
from .fee import fee_router
from .rate import rates_router
from .floor_plan import floor_plan_router
from .floor_plan_marker import floor_plan_marker_router
from .booked_date import booked_date_router
from .amenity import amenities_router
from .contact_request import contact_request_router
from .subscription import subscription_router
from .product import product_router


router = APIRouter(prefix="/api", tags=["API"])

router.include_router(user_router)
router.include_router(auth_router)
router.include_router(store_router)
router.include_router(location_router)
router.include_router(item_router)
router.include_router(member_router)
router.include_router(fee_router)
router.include_router(rates_router)
router.include_router(floor_plan_router)
router.include_router(floor_plan_marker_router)
router.include_router(booked_date_router)
router.include_router(amenities_router)
router.include_router(contact_request_router)
router.include_router(subscription_router)
router.include_router(product_router)

CFG = config()

stripe.api_key = CFG.STRIPE_SECRET_KEY


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
