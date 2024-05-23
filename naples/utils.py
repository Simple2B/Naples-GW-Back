import filetype
import smtplib
from email.message import EmailMessage

from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute


from naples.logger import log

EMAIL_ADDRESS = "varvarashcherbyna7@gmail.com"
EMAIL_PASSWORD = "tiigvauxcowxdlhf"


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def sendEmailVerify(token: str, user_email: str):
    # create email
    msg = EmailMessage()
    msg["Subject"] = "Email Verification"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = str(user_email)

    msg.set_content(
        f"Click the link to verify your email:\n http://127.0.0.1:5002/api/auth/verify-email?token={token}",
    )

    # send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    log(log.INFO, "Email verification sent to [%s]", user_email)

    return
