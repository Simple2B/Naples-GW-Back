import filetype
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
from .config import config

from naples import schemas as s
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


# def createMsgEmail(token: str, user_email: str) -> MIMEMultipart:
#     html_content = f"""
#         <html>
#             <body style='margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;'>
#             <div style='width: 100%; background: #efefef; border-radius: 10px; padding: 10px;'>
#                 <div style='margin: 0 auto; width: 90%; text-align: center;'>
#                 <h1 style='background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;'>Naples GW
#                 </h1>
#                 <div
#                     style='margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;'>
#                     <h3 style='margin-bottom: 100px; font-size: 24px;'>Click the link to verify your email!</h3>
#                     <p style='margin-bottom: 10px;'>Click the button below to verify your email address. If you did not sign up for
#                     an account, you can safely ignore this email.
#                     </p>
#                     <a style='display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;'
#                     href='{CFG.REDIRECT_URL}?token={token}' target='_blank'>
#                     Verify Email
#                     </a>
#                 </div>
#                 </div>
#             </div>
#             </body>
#         </html>
#     """

#     # create email
#     msg = MIMEMultipart()
#     msg["Subject"] = CFG.MAIL_SUBJECT
#     msg["From"] = f"{CFG.MAIL_USERNAME} <{CFG.MAIL_ADDRESS}>"
#     msg["To"] = str(user_email)
#     msg.attach(MIMEText(html_content, "html"))

#     return msg


def sendEmail(email: str, message: str, ses_client):
    # html_content = f"""
    #     <html>
    #         <body style='margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;'>
    #         <div style='width: 100%; background: #efefef; border-radius: 10px; padding: 10px;'>
    #             <div style='margin: 0 auto; width: 90%; text-align: center;'>
    #             <h1 style='background-color: rgba(0, 53, 102, 1); padding: 5px 10px; border-radius: 5px; color: white;'>Naples GW
    #             </h1>
    #             <div
    #                 style='margin: 30px auto; background: white; width: 40%; border-radius: 10px; padding: 50px; text-align: center;'>
    #                 <h3 style='margin-bottom: 100px; font-size: 24px;'>Click the link to verify your email!</h3>
    #                 <p style='margin-bottom: 10px;'>Click the button below to verify your email address. If you did not sign up for
    #                 an account, you can safely ignore this email.
    #                 </p>
    #                 <a style='display: block; margin: 0 auto; border: none; background-color: rgba(255, 214, 10, 1); color: white; width: 200px; line-height: 24px; padding: 10px; font-size: 24px; border-radius: 10px; cursor: pointer; text-decoration: none;'
    #                 href='{CFG.REDIRECT_URL}?token={token}' target='_blank'>
    #                 Verify Email
    #                 </a>
    #             </div>
    #             </div>
    #         </div>
    #         </body>
    #     </html>
    # """

    # create email
    # msg = MIMEMultipart()
    # msg["Subject"] = CFG.MAIL_SUBJECT
    # msg["From"] = f"{CFG.MAIL_USERNAME} <{CFG.MAIL_ADDRESS}>"
    # msg["To"] = str(user_email)
    # msg.attach(MIMEText(html_content, "html"))

    # try:
    #     ses_client.send_email()
    # catch():

    return


# def sendEmail(msg: MIMEMultipart):
#     with smtplib.SMTP_SSL(CFG.MAIL_HOST, CFG.MAIL_PORT) as smtp:
#         smtp.login(CFG.MAIL_ADDRESS, CFG.MAIL_PASSWORD)
#         smtp.send_message(msg)

#     return
