import filetype

from base64 import b64decode
from fastapi import APIRouter, Depends, HTTPException, status

from naples.database import get_db
from naples.dependency import get_s3_connect
from naples.logger import log
from naples import models as m, schemas as s, controllers as c
from naples.dependency.user import get_current_user
from naples.config import config


CFG = config()


files_router = APIRouter(prefix="/files", tags=["Files"])


@files_router.post("/upload/", response_model=s.FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: s.FileIn,
    current_user: m.User = Depends(get_current_user),
    db=Depends(get_db),
    s3_client=Depends(get_s3_connect),
):
    log(log.INFO, "Uploading file - {%s} for user {%s}", file.name, current_user.id)
    # TODO: verify that action is allowed for the user

    file_bytes: bytes = b64decode(file.file_base64)
    file_type = filetype.guess(file)

    if not file_type or file_type.mime.split("/")[0] != "image":
        log(log.INFO, "Invalid file type - %s", file_type.mime)
        raise HTTPException(
            status_code=400,
            detail="Invalid file type",
        )

    file_model: m.File = c.create_file(
        db=db,
        file=file_bytes,
        name=file.name,
        settings=CFG,
        s3_client=s3_client,
        extension=file_type.extension,
    )
    return s.FileOut.model_validate(file_model)


@files_router.delete("/{file_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_uuid: str,
    current_user: m.User = Depends(get_current_user),
    db=Depends(get_db),
    s3_client=Depends(get_s3_connect),
):
    log(log.INFO, "Deleting file - {%s} for user {%s}", file_uuid, current_user.id)

    file = db.scalar(m.File, m.File.uuid == file_uuid)

    if not file:
        log(log.INFO, "File not found - %s", file_uuid)
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    c.delete_file(db=db, file=file, s3_client=s3_client, settings=CFG)
