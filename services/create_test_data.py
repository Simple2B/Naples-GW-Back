import sys
from naples import models as m
from naples import schemas as s


def create_user(test_user: s.TestUser) -> m.User:

    """Create test user"""
    user = m.User(
        id=test_user.id,
        email=test_user.email,
        password=test_user.password,
        is_verified=True,
    )

    return user


def create_store(test_store: s.StoreOut) -> m.Store:
    """Create test store"""
    store = m.Store(
        uuid=test_store.uuid,
        name=test_store.name,
        header=test_store.header,
        sub_header=test_store.sub_header,
        url=test_store.url,
        logo_url=test_store.logo_url,
        about_us=test_store.about_us,
        email=test_store.email,
        phone=test_store.phone,
        instagram_url=test_store.instagram_url,
        messenger_url=test_store.messenger_url,
        user_id=test_store.user_id,
    )
    return store


def create_item(test_item: s.ItemOut, city_id: int) -> m.Item:
    """Create test item"""
    item = m.Item(
        uuid=test_item.uuid,
        name=test_item.name,
        description=test_item.description,
        latitude=test_item.latitude,
        longitude=test_item.longitude,
        address=test_item.address,
        size=test_item.size,
        bedrooms_count=test_item.bedrooms_count,
        bathrooms_count=test_item.bathrooms_count,
        stage=test_item.stage,
        category=test_item.category,
        type=test_item.type,
        store_id=test_item.store_id,
        realtor_id=test_item.realtor_id,
        city_id=city_id,
        price=test_item.price,
    )
    return item


def create_member(member: s.MemberOut) -> m.Member:
    """Create test member"""
    member = m.Member(
        uuid=member.uuid,
        name=member.name,
        email=member.email,
        phone=member.phone,
        instagram_url=member.instagram_url,
        messenger_url=member.messenger_url,
        avatar_url=member.avatar_url,
        store_id=member.store_id,
    )
    return member
