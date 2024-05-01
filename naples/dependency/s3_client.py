# from functools import lru_cache

from fastapi import Depends
import boto3

from naples.config import config, BaseConfig


# @lru_cache
def get_s3_connect(settings: BaseConfig = Depends(config)):
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
    )
    s3 = session.client("s3")
    return s3
