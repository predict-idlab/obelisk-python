"""Obelisk configuration."""
import logging


class ObeliskConfig:
    """Obelisk configuration."""

    CLIENT_ID = ''
    CLIENT_SECRET = ''

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
