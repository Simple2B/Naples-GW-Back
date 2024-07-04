import os
import csv


from fastapi import Depends, APIRouter, UploadFile, status, HTTPException
from fastapi_pagination import Page, Params, paginate

from fastapi.responses import FileResponse


from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session
import sqlalchemy as sa

from naples.controllers.file import get_file_type
from naples.dependency.admin import get_admin
from naples.dependency.s3_client import get_s3_connect
from naples import controllers as c, models as m, schemas as s


from naples.logger import log
from naples.dependency import get_current_user, get_current_user_store
from naples.database import get_db
from naples.routes.utils import get_stores_admin
from naples.utils import get_file_extension
from naples.config import config

from services.store.add_dns_record import (
    add_godaddy_dns_record,
    check_main_domain,
    check_subdomain_existence,
    delete_godaddy_dns_record,
    get_subdomain_from_url,
)


store_router = APIRouter(prefix="/stores", tags=["Stores"])

CFG = config()


@store_router.get(
    "/urls",
    status_code=status.HTTP_200_OK,
    response_model=s.TraefikData,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_stores_urls(
    db: Session = Depends(get_db),
):
    stores = db.scalars(sa.select(m.Store)).all()

    if not stores:
        log(log.ERROR, "Stores not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stores not found")

    data_stores = [
        s.TraefikStoreData(
            uuid=store.uuid,
            subdomain=get_subdomain_from_url(store.url) or store.uuid,
            store_url=store.url,
        )
        for store in stores
        if store.url
    ]

    traefik_http = s.TraefikHttp(
        routers={
            store.subdomain: s.TraefikRoute(
                rule=f"Host(`{store.store_url}`)",
                service=store.subdomain,
                tls=s.TraefikTLS(certResolver=CFG.CERT_RESOLVER),
            )
            for store in data_stores
        },
        services={
            store.subdomain: s.TraefikService(
                loadBalancer=s.TraefikLoadBalancer(servers=[s.TraefikServer(url=f"http://{CFG.WEB_SERVICE_NAME}")])
            )
            for store in data_stores
        },
    )
    return s.TraefikData(http=traefik_http)


@store_router.get(
    "/{store_url}",
    status_code=status.HTTP_200_OK,
    response_model=s.StoreOut,
    responses={
        404: {"description": "Store not found"},
    },
)
def get_store(
    store_url: str,
    db: Session = Depends(get_db),
):
    """Returns the store"""

    store: m.Store | None = db.scalar(sa.select(m.Store).where(m.Store.url == store_url))
    if not store:
        log(log.ERROR, "Store [%s] not found", store_url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store


@store_router.post("/", status_code=status.HTTP_201_CREATED, response_model=s.StoreOut)
def create_store(
    store: s.StoreIn,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    new_store: m.Store = m.Store(
        **store.model_dump(),
        user_id=current_user.id,
    )
    db.add(new_store)
    db.commit()
    log(log.INFO, "Created store [%s] for user [%s]", new_store.url, new_store.user_id)
    return new_store


@store_router.patch("/", status_code=status.HTTP_200_OK, response_model=s.StoreOut)
def update_store(
    store: s.StoreUpdateIn,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    if store.url is not None:
        log(log.INFO, "Updating url to [%s] for store [%s]", store.url, current_store.url)

        if check_main_domain(store.url):
            new_subdomain = get_subdomain_from_url(store.url)

            if not new_subdomain:
                log(log.ERROR, "New subdomain not found for store [%s]", store.url)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New subdomain not found")

            # check if the new subdomain already exists in db
            db_store = db.scalar(sa.select(m.Store).where(m.Store.url == store.url))

            if db_store:
                log(log.ERROR, "Store with url [%s] already exists", store.url)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store with url already exists")

            subdomain = get_subdomain_from_url(current_store.url)

            godaddy_subdomain = check_subdomain_existence(subdomain)

            if godaddy_subdomain and subdomain:
                delete_godaddy_dns_record(subdomain)
                log(log.INFO, "Old subdomain [%s] deleted", subdomain)

                # add new record with new url for the store in godaddy
                add_godaddy_dns_record(new_subdomain)

        current_store.url = store.url

        log(log.INFO, "store url  updated to [%s]", store.url)

    if store.email is not None:
        log(log.INFO, "Updating email to [%s] for store [%s]", store.email, current_store.url)
        current_store.email = store.email

    if store.instagram_url is not None:
        log(log.INFO, "Updating instagram url to [%s] for store [%s]", store.instagram_url, current_store.url)
        current_store.instagram_url = str(store.instagram_url)

    if store.messenger_url is not None:
        log(log.INFO, "Updating messenger url to [%s] for store [%s]", store.messenger_url, current_store.url)
        current_store.messenger_url = str(store.messenger_url)

    if store.phone is not None:
        log(log.INFO, "Updating phone to [%s] for store [%s]", store.phone, current_store.url)
        current_store.phone = store.phone

    if store.title_value is not None:
        log(log.INFO, "Updating title value to [%s] for store [%s]", store.title_value, current_store.url)
        current_store.title_value = store.title_value

    if store.title_color is not None:
        log(log.INFO, "Updating title color to [%s] for store [%s]", store.title_color.as_hex(), current_store.url)
        current_store.title_color = store.title_color.as_hex()

    if store.title_font_size is not None:
        log(log.INFO, "Updating title font size to [%s] for store [%s]", store.title_font_size, current_store.url)
        current_store.title_font_size = store.title_font_size

    if store.sub_title_value is not None:
        log(log.INFO, "Updating sub title value to [%s] for store [%s]", store.sub_title_value, current_store.url)
        current_store.sub_title_value = store.sub_title_value

    if store.sub_title_color is not None:
        log(
            log.INFO,
            "Updating sub title color to [%s] for store [%s]",
            store.sub_title_color.as_hex(),
            current_store.url,
        )
        current_store.sub_title_color = store.sub_title_color.as_hex()

    if store.sub_title_font_size is not None:
        log(
            log.INFO,
            "Updating sub title font size to [%s] for store [%s]",
            store.sub_title_font_size,
            current_store.url,
        )
        current_store.sub_title_font_size = store.sub_title_font_size

    if store.about_us_description is not None:
        log(
            log.INFO, "Updating description value to [%s] for store [%s]", store.about_us_description, current_store.url
        )
        current_store.about_us_description = store.about_us_description

    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Updated store [%s]", current_store.url)
    return current_store


@store_router.post(
    "/main_media",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Store not found"},
    },
)
def upload_store_main_media(
    main_media: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading main media for store [%s]", current_store.url)

    if current_store.main_media and not current_store.main_media.is_deleted:
        log(log.WARNING, "Store [%s] already has a main media. Marking as deleted", current_store.url)
        current_store.main_media.mark_as_deleted()
        db.commit()

    extension = get_file_extension(main_media)

    if not extension:
        log(log.ERROR, "Extension not found for main media [%s]", main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    file_type = get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "File type not supported for main media [%s]", main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not supported")

    main_media_file_model = c.create_file(
        db=db,
        file=main_media,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=file_type,
    )

    current_store.main_media_id = main_media_file_model.id
    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Main media [%s] uploaded for store [%s]", main_media_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/main_media",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_main_media(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting main media for store [%s]", current_store.url)
    if not current_store.main_media:
        log(log.ERROR, "Store [%s] does not have a main media", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a main media")

    current_store.main_media.mark_as_deleted()
    db.commit()

    log(log.INFO, "Main media deleted for store [%s]", current_store.url)


@store_router.post(
    "/logo",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
)
def upload_store_logo(
    logo: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    log(log.INFO, "Uploading logo for store [%s]", current_store.url)

    if current_store.logo and not current_store.logo.is_deleted:
        log(log.WARNING, "Store [%s] already has a logo. Marking as deleted", current_store.url)
        current_store.logo.mark_as_deleted()
        db.commit()

    if not logo.content_type == "image/svg+xml":
        log(log.ERROR, "Logo must be of type image/svg+xml. Received [%s]", logo.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo must be of type image/svg+xml")

    logo_file_model = c.create_file(
        db=db,
        file=logo,
        s3_client=s3_client,
        extension="svg",
        store_url=current_store.url,
        file_type=s.FileType.LOGO,
        content_type_override="image/svg+xml",
    )

    current_store.logo_id = logo_file_model.id
    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Logo [%s] uploaded for store [%s]", logo_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/logo",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_logo(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    log(log.INFO, "Deleting logo for store [%s]", current_store.url)
    if not current_store.logo:
        log(log.ERROR, "Store [%s] does not have a logo", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a logo")

    current_store.logo.mark_as_deleted()
    db.commit()

    log(log.INFO, "Logo deleted for store [%s]", current_store.url)


@store_router.post(
    "/about_us/main_media",
    status_code=status.HTTP_201_CREATED,
    response_model=s.StoreOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Store not found"},
    },
)
def upload_store_about_us_media(
    about_us_main_media: UploadFile,
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
    s3_client: S3Client = Depends(get_s3_connect),
):
    """Uploads the main media for the about us section of the store"""

    if current_store.about_us_main_media and not current_store.about_us_main_media.is_deleted:
        log(log.WARNING, "Store [%s] already has a main media. Marking as deleted", current_store.url)
        current_store.about_us_main_media.mark_as_deleted()
        db.commit()

    extension = get_file_extension(about_us_main_media)

    if not extension:
        log(log.ERROR, "Extension not found for main media [%s]", about_us_main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    file_type = get_file_type(extension)

    if file_type == s.FileType.UNKNOWN:
        log(log.ERROR, "File type not supported for main media [%s]", about_us_main_media.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not supported")

    about_us_main_media_file_model = c.create_file(
        db=db,
        file=about_us_main_media,
        s3_client=s3_client,
        extension=extension,
        store_url=current_store.url,
        file_type=file_type,
    )

    current_store.about_us_main_media_id = about_us_main_media_file_model.id

    db.commit()
    db.refresh(current_store)

    log(log.INFO, "Main media [%s] uploaded for store [%s]", about_us_main_media_file_model.name, current_store.url)

    return current_store


@store_router.delete(
    "/about_us/main_media",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Store not found"},
    },
)
def delete_store_about_us_media(
    db: Session = Depends(get_db),
    current_store: m.Store = Depends(get_current_user_store),
):
    """Deletes the main media for the about us section of the store"""

    log(log.INFO, "Deleting main media for store [%s]", current_store.url)

    if not current_store.about_us_main_media:
        log(log.ERROR, "Store [%s] does not have a main media", current_store.url)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store does not have a main media")

    current_store.about_us_main_media.mark_as_deleted()
    db.commit()

    log(log.INFO, "About us main media deleted for store [%s]", current_store.url)


# get info stores for admin panel
# TODO: will be finishing
@store_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.StoreAdminOut],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Stores not found"}},
    dependencies=[Depends(get_admin)],
)
def get_stores(
    db: Session = Depends(get_db),
    params: Params = Depends(),
    search: str | None = None,
    subscription_status: s.StoreStatus | None = None,
):
    """Returns the stores for the admin panel"""

    stores = get_stores_admin(db, search, subscription_status if subscription_status else None)
    return paginate(stores, params)


@store_router.post(
    "/report/download",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Stores not found"},
    },
    dependencies=[Depends(get_admin)],
)
def get_stores_report(
    db: Session = Depends(get_db),
    search: str | None = None,
    subscription_status: s.StoreStatus | None = None,
):
    """Create report of the stores for the admin panel"""

    stores = get_stores_admin(db, search, subscription_status if subscription_status else None)

    if not stores:
        log(log.ERROR, "Stores not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stores not found",
        )

    with open(
        os.path.join(CFG.REPORTS_DIR, CFG.STORES_REPORT_FILE),
        "w",
        newline="",
    ) as report_file:
        report = csv.writer(report_file)
        data = [
            [
                "User Name",
                "Email",
                "Phone",
                "Is Blocked",
                "Subscription Status",
                "Created At",
                "Store Url",
                "№ of properties",
            ]
        ]

        for store in stores:
            user_name = store.user.first_name + " " + store.user.last_name
            email = store.user.email
            phone = store.user.phone
            is_blocked = str(store.user.is_blocked).lower()
            status_subscription = store.status.value.upper()
            created_at = store.user.created_at.strftime("%H:%M %b %d %Y")
            store_url = store.url
            properties = str(store.items_count)
            data.append(
                [
                    user_name,
                    email,
                    phone,
                    is_blocked,
                    status_subscription,
                    created_at,
                    store_url,
                    properties,
                ]
            )
        log(
            log.INFO,
            "Create report data [%s] for admin panel ",
            data,
        )

        report.writerows(data)

        log(
            log.INFO,
            "Write data (count of stores in data [%d]) to csv file",
            len(data),
        )

    return FileResponse(os.path.join(CFG.REPORTS_DIR, CFG.STORES_REPORT_FILE))
