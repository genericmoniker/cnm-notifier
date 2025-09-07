from email.message import EmailMessage


class Mailer:
    """Simple interface to send email messages using the smtplib module."""

    def __init__(self, smtp):
        self._smtp = smtp

    def send_message(self, recipients, sender, subject, body):
        msg = EmailMessage()
        msg["To"] = recipients
        msg["From"] = sender
        msg["Subject"] = subject
        subtype = "html" if "<html>" in body else "plain"
        msg.set_content(body, subtype=subtype)
        self._smtp.send_message(msg)
