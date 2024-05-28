import filetype
from datetime import datetime, timedelta, UTC

from mypy_boto3_ses import SESClient
from botocore.exceptions import ClientError


from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
from .config import config

from naples.logger import log


CFG = config()


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def createMsgEmail(token: str, verify_router: str) -> str:
    html_content = f"""
        <html>
            <body style='margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;'>
            <div style='width: 100%; background: #efefef; border-radius: 10px; padding: 10px;'>
                <div style='margin: 0 auto; width: 90%; text-align: center;'>
                <h1 style='background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;'>Naples GW
                </h1>
                <div
                    style='margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;'>
                    <h3 style='margin-bottom: 100px; font-size: 24px;'>Click the link to verify your email!</h3>
                    <p style='margin-bottom: 10px;'>Click the button below to verify your email address. If you did not sign up for
                    an account, you can safely ignore this email.
                    </p>
                    <a style='display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;'
                    href='{CFG.REDIRECT_URL}{verify_router}?token={token}' target='_blank'>
                    Verify Email
                    </a>
                </div>
                </div>
            </div>
            </body>
        </html>
    """

    return html_content


def createMsgEmailChangePassword(token: str, verify_router: str) -> str:
    html_content = f"""
        <html>
            <body style='margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;'>
            <div style='width: 100%; background: #efefef; border-radius: 10px; padding: 10px;'>
                <div style='margin: 0 auto; width: 90%; text-align: center;'>
                <h1 style='background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;'>Naples GW
                </h1>
                <div
                    style='margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;'>
                    <h3 style='margin-bottom: 100px; font-size: 24px;'>Click the link to change your password!</h3>
                    <p style='margin-bottom: 10px;'>Click the button below to change your password. If you did not request a password change, you can safely ignore this email.
                    </p>
                    <a style='display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;'
                    href='{CFG.REDIRECT_URL}{verify_router}?token={token}' target='_blank'>
                    Change Password
                    </a>
                </div>
                </div>
            </div>
            </body>
        </html>
    """

    return html_content


def sendEmail(email: str, message: str, ses_client: SESClient):
    try:
        # the contents of the email.
        response = ses_client.send_email(
            Destination={
                "ToAddresses": [
                    email,
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CFG.CHARSET,
                        "Data": message,
                    },
                    "Text": {
                        "Charset": CFG.CHARSET,
                        "Data": CFG.MAIL_BODY_TEXT,
                    },
                },
                "Subject": {
                    "Charset": CFG.CHARSET,
                    "Data": CFG.MAIL_SUBJECT,
                },
            },
            Source=CFG.MAIL_DEFAULT_SENDER,
        )
        log(log.INFO, "Email sent! Message ID: [%s]", response["MessageId"])
        log(log.INFO, "Email sent response [%s]", response)
    except ClientError as e:
        log(log.ERROR, "Email not sent! [%s]", e.response["Error"]["Message"])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not sent!")


def get_expire_datatime() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=CFG.ACCESS_TOKEN_EXPIRE_MINUTES)
