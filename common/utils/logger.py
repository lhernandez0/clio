import logging
import sys


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Output logs to stdout
            # logging.FileHandler("app.log")
        ],
    )
    logger = logging.getLogger()
    return logger
