"""Main entry point for the Pi-Hole Notifier application."""
import logging
import sys

import config
import cnm
import log
import notify


logger = logging.getLogger(__name__)


def main():
    log.setup_logging(level=logging.INFO)
    logger.info("===== CNM Notifier Startup =====")

    conf = config.Config()

    try:
        cnm.monitor(conf, notify)
    except Exception as ex:
        logger.error(ex)
        return 1


if __name__ == "__main__":
    sys.exit(main())
