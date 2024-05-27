from functools import cache

import boto3
from mypy_boto3_ses import SESClient


from naples.config import config


@cache
def get_ses_client() -> SESClient:
    settings = config()
    ses = boto3.client(
        "ses",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.MAIL_USERNAME,
        aws_secret_access_key=settings.MAIL_PASSWORD,
    )
    return ses
