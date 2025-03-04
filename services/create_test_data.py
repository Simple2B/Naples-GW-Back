from naples import models as m
from naples import schemas as s


def create_user(test_user: s.TestUser) -> m.User:
    """Create test user"""
    user = m.User(
        uuid=test_user.uuid,
        first_name=test_user.first_name,
        last_name=test_user.last_name,
        email=test_user.email,
        password=test_user.password,
        role=test_user.role,
        is_verified=True,
    )

    return user


def create_test_user(test_user: s.TestUser) -> m.User:
    """Create test user"""
    user = m.User(
        uuid=test_user.uuid,
        email=test_user.email,
        first_name=test_user.first_name,
        last_name=test_user.last_name,
        password=test_user.password,
        role=test_user.role,
        is_verified=True,
    )

    return user


def create_store(test_store: s.TestStore) -> m.Store:
    """Create test store"""
    store = m.Store(
        url=test_store.url,
        email=test_store.email,
        phone=test_store.phone,
        instagram_url=test_store.instagram_url,
        messenger_url=test_store.messenger_url,
        user_id=test_store.user_id,
        title_value=test_store.title_value,
        title_color=test_store.title_color,
        title_font_size=test_store.title_font_size,
        sub_title_value=test_store.sub_title_value,
        sub_title_color=test_store.sub_title_color,
        sub_title_font_size=test_store.sub_title_font_size,
    )
    return store


def create_item(test_item: s.TestItem) -> m.Item:
    """Create test item"""

    item = m.Item(
        name=test_item.name,
        store_id=test_item.store_id,
        realtor_id=test_item.realtor_id,
        nightly=test_item.nightly,
        monthly=test_item.monthly,
        annual=test_item.annual,
        stage=test_item.stage,
        adults=test_item.adults,
    )
    return item


def create_member(member: s.TestMember) -> m.Member:
    """Create test member"""
    member = m.Member(
        name=member.name,
        email=member.email,
        phone=member.phone,
        instagram_url=member.instagram_url,
        messenger_url=member.messenger_url,
        store_id=member.store_id,
    )
    return member
