from dataclasses import asdict
import json
import logging
from pathlib import Path
import smtplib

from cnm import NetworkStatus
import mailer

logger = logging.getLogger(__name__)


FIREWALL_STATUS_ONLINE = 3  # TODO: What are the possible statuses? Make an Enum.
PASSWORD_EXPIRY_NOTIFY_DAYS = 3  # Number of days before expiry to notify.


def update_status(config, status):
    """Update the status of a network, sending a notification if needed."""
    last_status = _load_status(status.network_id)
    _save_status(status)
    if not last_status:
        return

    # Notify of firewall status changes.
    if status.firewall_status != last_status.firewall_status:
        if status.firewall_status == FIREWALL_STATUS_ONLINE:
            online(config, status)
        else:
            offline(config, status)

    # Notify of Lehi SSID password expiry changes.
    if status.lehi_expiry_days != last_status.lehi_expiry_days:
        if status.lehi_expiry_days <= PASSWORD_EXPIRY_NOTIFY_DAYS:
            password_expiring(config, status)


def offline(config, status):
    """Notify that a firewall is offline."""
    subject = f"[CNM] ❌ {status.network_name} is offline"
    body = (
        f"The firewall {status.network_id} at {status.network_name} is offline "
        f"({status.firewall_status})."
    )
    _send_mail(config, subject, body)
    logger.info("Sent offline notification: %s", subject)


def online(config, status):
    """Notify that a firewall is online after having been offline."""
    subject = f"[CNM] ✅ {status.network_name} is back online"
    body = (
        f"The firewall {status.network_id} at {status.network_name} is online "
        f"({status.firewall_status})."
    )
    _send_mail(config, subject, body)
    logger.info("Sent online notification: %s", subject)


def password_expiring(config, status):
    """Notify that the Lehi SSID password is expiring soon/has expired."""
    subject = f"[CNM] ⚠ {status.network_name} Lehi SSID password expiring"
    body = f"The Lehi SSID password for {status.network_id} at {status.network_name} "
    body += ({
        0: "has expired.",
        1: "will expire in 1 day.",
    }.get(status.lehi_expiry_days, f"will expire in {status.lehi_expiry_days} days."))
    _send_mail(config, subject, body)
    logger.info("Sent password expiring notification: %s", subject)


def error(config, ex):
    """Notify that an error occurred."""
    subject = "[CNM] Monitoring error"
    body = f"An error occurred while monitoring CNM: {ex}"
    _send_mail(config, subject, body)
    logger.info("Sent error notification: %s", subject)


def _load_status(network_id) -> NetworkStatus | None:
    """Load the status for a network from a file."""
    path = _get_status_file_path(network_id)
    if path.exists():
        try:
            with path.open("r") as file:
                return NetworkStatus(**json.load(file))
        except Exception:
            logger.exception("Error loading last status.")
            return None
    logger.debug("No last status found.")
    return None


def _save_status(status: NetworkStatus) -> None:
    """Save the status for a network to a file."""
    path = _get_status_file_path(status.network_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as file:
            json.dump(asdict(status), file)
    except Exception:
        logger.exception("Error saving last status.")


def _get_status_file_path(network_id) -> Path:
    return Path(__file__).parent / "data" / f"{network_id}.json"


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
