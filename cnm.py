import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

import requests
from playwright.sync_api import sync_playwright

CNM_URL = "https://cnm.churchofjesuschrist.org/"
AUTH_URL = "https://id.churchofjesuschrist.org"
FIREWALL_URL = "https://cnm.churchofjesuschrist.org/Networks/Meraki/firewall/api/{}"
SSID_URL = "https://cnm.churchofjesuschrist.org/Networks/Meraki/ssid/api/{}"
NORMAL_POLL_INTERVAL = timedelta(minutes=60)
OFFLINE_POLL_INTERVAL = timedelta(minutes=5)

logger = logging.getLogger(__name__)


@dataclass
class NetworkStatus:
    """Network status, including the status of a firewall and Lehi SSID expiry."""

    network_id: str
    firewall_status: int
    network_name: str
    lehi_expiry_days: int | None = None


class MonitorConfigError(Exception):
    """Raised when there is an error in the monitor configuration."""


def monitor(config, notify):
    """Monitor the network status of a network.

    The monitor blocks indefinitely, polling the network status.

    Args:
        config: the configuration
        notify: the notification module with functions to call when
            a network status should trigger a notification.
    """
    if not config.CNM_USERNAME or not config.CNM_PASSWORD:
        raise MonitorConfigError("CNM username or password not configured.")

    if not config.CNM_NETWORKS:
        raise MonitorConfigError("No CNM networks configured.")

    logger.info("Starting to monitor Church Network Manager...")

    session = requests.Session()
    while True:
        any_offline = False
        try:
            for network_id in config.CNM_NETWORKS:
                status = _get_network_status(
                    network_id, session, config.CNM_USERNAME, config.CNM_PASSWORD
                )
                logger.info(str(status))
                notify.update_status(config, status)
                if status.firewall_status != notify.FIREWALL_STATUS_ONLINE:
                    any_offline = True
        except Exception as ex:
            logger.error("Error monitoring CNM: %r %s", ex, ex)
            notify.error(config, ex)

        # Poll more frequently if any network is offline to catch fixes sooner.
        poll_interval = OFFLINE_POLL_INTERVAL if any_offline else NORMAL_POLL_INTERVAL
        time.sleep(poll_interval.total_seconds())


def _get_network_status(network_id, session, username, password):
    """Get the status of a network

    :param network_id: ID/serial number of the network/firewall
    :return: the network status of the network
    """
    # Get the firewall status.
    response = session.get(FIREWALL_URL.format(network_id), allow_redirects=False)
    if response.status_code == 302 and AUTH_URL in response.headers["Location"]:
        logger.info("Logging in to CNM...")
        _login(session, username, password)
        response = session.get(FIREWALL_URL.format(network_id), allow_redirects=False)
    response.raise_for_status()
    data_fw = response.json()

    # Get the Lehi SSID password expiry.
    response = session.get(SSID_URL.format(network_id), allow_redirects=False)
    response.raise_for_status()
    data_ssid = response.json()
    lehi_ssid = next((ssid for ssid in data_ssid if ssid["name"] == "Lehi"), None)
    if lehi_ssid:
        lehi_expiry_days = lehi_ssid["daysUntilExpire"]
    else:
        lehi_expiry_days = None
        logger.warning("Lehi SSID not found for network %s", network_id)

    return NetworkStatus(
        network_id=data_fw["serialNumber"],
        network_name=data_fw["networkName"],
        firewall_status=data_fw["status"],
        lehi_expiry_days=lehi_expiry_days,
    )


def _login(session, username, password):
    """Log in to the CNM.

    :param username: the username
    :param password: the password
    """
    # This takes around 10 seconds to complete on my development machine...
    # To debug, you can try running the browser in headless=False mode (see the
    # playwright_browser context manager).
    with sync_playwright() as playwright:
        with playwright_browser(playwright) as browser:
            with playwright_context(browser) as context:
                page = context.new_page()
                page.goto(CNM_URL)

                page.fill('input[id="username-input"]', username)
                page.keyboard.press("Enter")

                page.fill('input[type="password"]', password)
                page.keyboard.press("Enter")
                page.wait_for_url(CNM_URL)

                # Copy cookies to the requests session.
                session.cookies.clear()
                for cookie in context.cookies():
                    session.cookies.set(cookie["name"], cookie["value"])


@contextmanager
def playwright_browser(playwright):
    browser = playwright.chromium.launch(headless=True)
    try:
        yield browser
    finally:
        browser.close()


@contextmanager
def playwright_context(browser):
    context = browser.new_context()
    try:
        yield context
    finally:
        context.close()
