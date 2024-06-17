import filetype
from datetime import datetime, timedelta, UTC
from mypy_boto3_ses import SESClient

from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from .config import config

import naples.schemas as s
import naples.models as m
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


def sendEmailAmazonSES(emailContent: s.EmailAmazonSESContent, ses_client: SESClient):
    # the contents of the email.
    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                emailContent.recipient_email,
            ],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": emailContent.charset,
                    "Data": emailContent.message,
                },
                "Text": {
                    "Charset": emailContent.charset,
                    "Data": emailContent.mail_body_text,
                },
            },
            "Subject": {
                "Charset": emailContent.charset,
                "Data": emailContent.mail_subject,
            },
        },
        Source=emailContent.sender_email,
    )
    log(log.INFO, "Email sent! Message ID: [%s]", response["MessageId"])
    log(log.INFO, "Email sent response [%s]", response)
    return response


def get_expire_datatime() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=CFG.ACCESS_TOKEN_EXPIRE_MINUTES)


def delete_user_with_store(db: Session, user: m.User) -> None:
    db.delete(user.store)
    db.delete(user)
    db.commit()
    return


def get_link_type(link: str) -> str:
    if s.LinkType.YouTubeVideo.value in link or s.LinkType.YouTuVideo.value in link:
        log(log.INFO, "link is youtube")
        return s.LinkType.YouTubeVideo.value

    return s.LinkType.UNKNOWN.value
