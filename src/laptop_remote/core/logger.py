"""Centralized logging configuration for Laptop Remote."""

import logging
import sys

LOGGER_NAME = "laptop_remote"
logger = logging.getLogger(LOGGER_NAME)


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure log level and formatting based on CLI flags.

    - quiet: Only WARNING and ERROR logs are emitted. Banner is silenced.
    - verbose: Full DEBUG logs emitted including packet tracing and input events.
    - default: INFO level with concise runtime output.
    """
    root_logger = logging.getLogger(LOGGER_NAME)
    werkzeug_logger = logging.getLogger("werkzeug")
    socketio_logger = logging.getLogger("socketio")
    engineio_logger = logging.getLogger("engineio")

    if quiet:
        level = logging.WARNING
        werkzeug_logger.setLevel(logging.ERROR)
        socketio_logger.setLevel(logging.ERROR)
        engineio_logger.setLevel(logging.ERROR)
    elif verbose:
        level = logging.DEBUG
        werkzeug_logger.setLevel(logging.INFO)
        socketio_logger.setLevel(logging.INFO)
        engineio_logger.setLevel(logging.INFO)
    else:
        level = logging.INFO
        werkzeug_logger.setLevel(logging.WARNING)
        socketio_logger.setLevel(logging.WARNING)
        engineio_logger.setLevel(logging.WARNING)

    root_logger.setLevel(level)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
