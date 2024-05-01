from fastapi import Depends, Form

from sqlalchemy.orm import Session

from naples.database import get_db
import naples.models as m
from naples.logger import log


def get_item(
    name: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    size: int = Form(...),
    price: int = Form(...),
    bedrooms_count: int = Form(...),
    bathrooms_count: int = Form(...),
    city_uuid: str = Form(...),
    stage: str = Form(...),
    category: str = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
) -> m.Item:
    """Create and then return the current item from the database"""
    item = m.Item(
        name=name,
        description=description,
        latitude=latitude,
        longitude=longitude,
        address=address,
        size=size,
        price=price,
        bedrooms_count=bedrooms_count,
        bathrooms_count=bathrooms_count,
        city_uuid=city_uuid,
        stage=stage,
        category=category,
        type=type,
    )
    db.add(item)
    log(log.INFO, "Item [%s] add", item.name)
    return item
