import smtplib
from email.message import EmailMessage

import filetype


def send_email(username, passkey, subject_text, messagetxt, receiverlist, files):
    """Sends an email through gmail with attachements.

    Parameters
    ----------
    username : str
        Name of the sender email.
    passkey : str
        Password for the email account
    subject_text : str
        The Subject text for the email
    message_text : str
        The message text for the email
    receiverlist : list
        A list of email addresses.
    files : list
        A list of files that will be sent.
    """
    smtp_server = "smtp.gmail.com"
    port = 587

    message = EmailMessage()
    message["Subject"] = subject_text
    message["From"] = username
    message["To"] = ", ".join(receiverlist)
    message.set_content(messagetxt)

    for file in files:
        with open(file, "rb") as f:
            image_data = f.read()
            image_type = filetype.guess(f.name).extension
            image_name = f.name
        message.add_attachment(
            image_data, maintype="image", subtype=image_type, filename=image_name
        )

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
