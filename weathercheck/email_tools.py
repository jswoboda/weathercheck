import imghdr
import smtplib
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase


def send_email(username, passkey, subject_text, messagetxt, receiverlist, files):
    smtp_server = "smtp.gmail.com"
    port = 587

    message = EmailMessage()
    for file in files:
        with open(file, "rb") as f:
            image_data = f.read()
            image_type = imghdr.what(f.name)
            image_name = f.name
        message.add_attachment(
            image_data, maintype="image", subtype=image_type, filename=image_name
        )

    message["Subject"] = subject_text
    message["From"] = username
    message["To"] = ", ".join(receiverlist)
    message.set_content(messagetxt)
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(username, passkey)
        server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your username and password.")
    except smtplib.SMTPConnectError:
        print("Failed to connect to the SMTP server.")
    except smtplib.SMTPRecipientsRefused:
        print("One or more recipients were rejected.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        server.quit()
