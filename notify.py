import logging
import smtplib
import mailer

logger = logging.getLogger(__name__)


def notify_offline(config, status):
    """Notify that a firewall is offline."""
    subject = f"[CNM] {status.network_name} is offline"
    body = f"The firewall {status.firewall_sn} at {status.network_name} is offline ({status.firewall_status})."
    _send_mail(config, subject, body)


def notify_error(config, ex):
    """Notify that an error occurred."""
    subject = "[CNM] Monitoring error"
    body = f"An error occurred while monitoring CNM: {ex}"
    _send_mail(config, subject, body)


def _send_mail(config, subject, body):
    try:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as client:
            client.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            mail = mailer.Mailer(client)
            mail.send_message(
                config.MAIL_RECIPIENTS,
                config.MAIL_SENDER,
                subject,
                body,
            )
    except Exception:
        logger.exception("Error sending mail.")
