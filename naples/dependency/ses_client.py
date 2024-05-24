from functools import cache

import boto3


from naples.config import config


@cache
def get_ses_client():
    settings = config()
    session = boto3.Session(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_SES_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SES_SECRET_KEY,
    )
    ses = session.client("ses")
    return ses
