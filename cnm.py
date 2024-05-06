from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
import logging
import time
from playwright.sync_api import sync_playwright
import requests

CNM_URL = "https://cnm.churchofjesuschrist.org/"
AUTH_URL = "https://id.churchofjesuschrist.org"
FIREWALL_URL = "https://cnm.churchofjesuschrist.org/Networks/Meraki/firewall/api/{}"
POLL_INTERVAL_SECONDS = timedelta(minutes=60)


@dataclass
class NetworkStatus:
    """The network status of a firewall."""

    firewall_sn: str
    firewall_status: int
    network_name: str


logger = logging.getLogger(__name__)


class MonitorConfigError(Exception):
    """Raised when there is an error in the monitor configuration."""


def monitor(config, offline_callback, error_callback):
    """Monitor the network status of a firewall.

    The monitor blocks indefinitely, polling the network status.

    Args:
        config: the configuration
        offline_callback: A callback to call when the firewall is offline. The
            callback should accept the configuration and the network status as
            arguments.
        error_callback: A callback to call when an error occurs. The callback should
            accept the configuration and the error (exception) as an argument.
    """
    if not config.CNM_USERNAME or not config.CNM_PASSWORD:
        raise MonitorConfigError("CNM username or password not configured.")

    if not config.CNM_FIREWALLS:
        raise MonitorConfigError("No CNM firewalls configured.")

    logger.info("Monitoring Church Network Manager...")

    session = requests.Session()
    while True:
        try:
            for firewall_sn in config.CNM_FIREWALLS:
                status = _get_network_status(
                    firewall_sn, session, config.CNM_USERNAME, config.CNM_PASSWORD
                )
                logger.info(
                    "Firewall %s at %s status: %s",
                    status.firewall_sn,
                    status.network_name,
                    status.firewall_status,
                )
                if status.firewall_status != 3:  # TODO: What are the possible statuses?
                    offline_callback(config, status)
        except Exception as ex:
            logger.error("Error monitoring CNM: %s", ex)
            error_callback(config, ex)

        time.sleep(POLL_INTERVAL_SECONDS.total_seconds())


def _get_network_status(firewall_sn, session, username, password):
    """Check the network status of a firewall

    :param firewall_sn: the serial number of the firewall
    :return: the network status of the firewall
    """
    response = session.get(FIREWALL_URL.format(firewall_sn), allow_redirects=False)
    if response.status_code == 302 and AUTH_URL in response.headers["Location"]:
        logger.info("Logging in to CNM...")
        _login(session, username, password)
        response = session.get(FIREWALL_URL.format(firewall_sn), allow_redirects=False)
    response.raise_for_status()
    data = response.json()
    return NetworkStatus(
        data["serialNumber"], data["firewallStatus"], data["networkName"]
    )


def _login(session, username, password):
    """Log in to the CNM.

    :param username: the username
    :param password: the password
    """
    # This takes around 10 seconds to complete on my development machine...
    with sync_playwright() as playwright:
        with playwright_browser(playwright) as browser:
            with playwright_context(browser) as context:
                page = context.new_page()
                page.goto(CNM_URL)

                page.fill('input[name="identifier"]', username)
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
