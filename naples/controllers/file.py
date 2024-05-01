from io import BytesIO

from fastapi import status, HTTPException
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from naples import models as m
from naples.logger import log
from naples.config import MergedConfig
from naples.models.utils import create_uuid


def create_file(
    db: Session,
    file: bytes,
    name: str,
    settings: MergedConfig,
    s3_client,
    extension: str,
    type: str,
    owner_type: str,
    owner_uuid: int,
) -> m.File:
    try:
        file_uuid = create_uuid()
        filename = f"{file_uuid}_{name}"
        key = f"posts/files/{filename}".rsplit(".", 1)[0] + f".{extension}"
        log(log.INFO, "key is %s", key)

        # Create a BytesIO stream from the file bytes
        file_stream = BytesIO(file)

        s3_client.upload_fileobj(
            file_stream,  # Pass the BytesIO stream
            settings.AWS_S3_BUCKET_NAME,
            key,
            ExtraArgs={"ACL": "public-read-write"},
        )
    except ClientError as e:
        log(log.ERROR, "Error uploading file to S3 - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error while uploading file to storage",
        )

    file = m.File(
        type=type,
        owner_type=owner_type,
        owner_uuid=owner_uuid,
        uuid=file_uuid,
        url=f"{settings.AWS_S3_BUCKET_URL}/{key}",
        original_name=name,
        name=f"{filename}",
        key=key,
    )
    db.add(file)
    try:
        db.commit()
    except SQLAlchemyError as e:
        log(log.INFO, "file [%s] was not created:\n %s", file.name, e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="file exists")
    db.refresh(file)
    log(log.INFO, "file [%s] was created", file.name)
    return file


def delete_file(
    db: Session,
    file: m.File,
    settings: MergedConfig,
    s3_client,
) -> None:
    try:
        s3_client.delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=file.key)
    except ClientError as e:
        log(log.ERROR, "Error deleting file from S3 - [%s]", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error occurred while deleting file from S3",
        )
    try:
        db.delete(file)
        db.commit()
    except SQLAlchemyError as e:
        log(log.INFO, "file [%s] was not deleted:\n %s", file.name, e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="file exists")
