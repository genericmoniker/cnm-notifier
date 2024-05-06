import datetime
import logging
import sys


def setup_logging(level=logging.DEBUG):
    """Set up logging to stdout."""
    fmt = "{asctime} {levelname:8}: {message}"
    formatter = ISO8601Formatter(fmt, style="{")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    return root_logger


class ISO8601Formatter(logging.Formatter):
    """Formatter to output ISO8601 date/time with milliseconds and timezone."""

    def formatTime(self, record, datefmt=None):
        return (
            datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc)
            .astimezone()
            .isoformat()
        )
