"""
Logging setup module for structured and colorized console logging.

This module provides a function to set up a standardized logger with
configurable log levels and colored console output.
"""

import logging
import sys
from typing import Optional

try:
    import colorlog  # Optional dependency for colored output

    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logger(name: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Setup a structured logger with console output.

    This function creates a logger with a standardized format, supporting
    colored output when the colorlog library is available. The log level
    can be configured, and the logger is named after the calling module.

    Args:
        name (str, optional): Name of the logger.
            Defaults to None, which uses the root logger.
        log_level (str, optional): Logging level.
            Supported levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
            Defaults to "INFO".

    Returns:
        logging.Logger: Configured logger instance.

    Raises:
        ValueError: If an invalid log level is provided.
    """
    # Validate and convert log level
    log_level = log_level.upper()
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    if log_level not in log_levels:
        raise ValueError(
            f"Invalid log level: {log_level}. "
            f"Choose from {', '.join(log_levels.keys())}"
        )

    # Create logger
    logger = logging.getLogger(name or __name__)
    logger.setLevel(log_levels[log_level])

    # Clear any existing handlers to prevent duplicate logs
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_levels[log_level])

    # Define log format
    formatter_base = "[%(asctime)s] %(levelname)s - %(module)s - %(message)s"
    date_formatter = "%Y-%m-%d %H:%M:%S"

    # Use colorlog if available, otherwise use standard logging
    if COLORLOG_AVAILABLE:
        # Color mapping for different log levels
        log_colors = {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }

        # Create colored formatter
        formatter = colorlog.ColoredFormatter(
            f"%(log_color)s{formatter_base}",
            log_colors=log_colors,
            datefmt=date_formatter,
        )
    else:
        # Fallback to standard logging formatter
        formatter = logging.Formatter(fmt=formatter_base, datefmt=date_formatter)

    # Set formatter for console handler
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


# Example usage when module is run directly
if __name__ == "__main__":
    # Demonstrate logger usage with different log levels
    logger = setup_logger(name=__name__, log_level="DEBUG")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
