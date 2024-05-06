import json
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


class Config:
    """Configuration for the CNM Notifier application.

    The configuration is loaded from secrets when available, with fallback to
    environment variables.
    """

    def __init__(self) -> None:
        # Load config from secrets, if possible.
        try:
            # The secret file is mounted in /run/secrets named after the secret
            # name (notifier_config), not the original name of the file
            # (notifier_config.json).
            secret_file = Path("/run/secrets/notifier_config")
            self._secret_conf = json.loads(secret_file.read_text())
            logger.info("Using config from secrets or environment.")
        except Exception as ex:
            self._secret_conf = {}
            logger.info("Using config from environment only. %s", ex)

        # Mail settings
        self.SMTP_HOST = self._get("SMTP_HOST")
        self.SMTP_PORT = self._get("SMTP_PORT")  # defaults to 465
        self.SMTP_USERNAME = self._get("SMTP_USERNAME")
        self.SMTP_PASSWORD = self._get("SMTP_PASSWORD")
        self.MAIL_SENDER = self._get("MAIL_SENDER")  # may be ignored by SMTP server
        self.MAIL_RECIPIENTS = self._get("MAIL_RECIPIENTS")

        # CNM settings
        self.CNM_USERNAME = self._get("CNM_USERNAME")
        self.CNM_PASSWORD = self._get("CNM_PASSWORD")
        firewalls = self._get("CNM_FIREWALLS").split(",")
        self.CNM_FIREWALLS = [fw.strip() for fw in firewalls]

    def _get(self, key):
        """Get a config value.

        Tries to get the value from a secret file, otherwise from an environment
        variable. See https://docs.docker.com/compose/compose-file/#secrets
        """
        return self._secret_conf.get(key, os.getenv(key))
