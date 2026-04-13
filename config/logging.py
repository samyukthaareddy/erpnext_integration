"""
Centralized logging configuration for the ERPNext CRM Integration service.

Sets up structured logging with appropriate handlers for different environments.
"""

import logging
import logging.config
import sys
from config.settings import get_config

# Get the active configuration
config = get_config()

# Define logging levels
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s - %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": config.LOG_LEVEL,
            "formatter": "verbose",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": config.LOG_LEVEL,
            "formatter": "verbose",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {
        "level": config.LOG_LEVEL,
        "handlers": ["console", "file"] if not config.DEBUG else ["console"],
    },
    "loggers": {
        "flask": {
            "level": config.LOG_LEVEL,
            "handlers": ["console", "file"] if not config.DEBUG else ["console"],
        },
        "app": {
            "level": config.LOG_LEVEL,
            "handlers": ["console", "file"] if not config.DEBUG else ["console"],
        },
    },
}


def setup_logging():
    """
    Configure logging for the application.

    Ensures the logs directory exists and sets up handlers.
    """
    import os

    # Ensure logs directory exists
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name):
    """
    Get or create a logger with the given name.

    Args:
        name (str): The name of the logger (usually __name__)

    Returns:
        logging.Logger: A configured logger instance
    """
    setup_logging()
    return logging.getLogger(name)
