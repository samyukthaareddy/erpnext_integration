"""
Configuration management for the ERPNext CRM Integration service.

Loads configuration from environment variables with sensible defaults.
Different configurations for development, testing, and production.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""

    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

    # ERPNext Integration
    ERPNEXT_BASE_URL = os.getenv("ERPNEXT_BASE_URL", "http://localhost:8000")
    ERPNEXT_API_KEY = os.getenv("ERPNEXT_API_KEY", "")
    ERPNEXT_API_SECRET = os.getenv("ERPNEXT_API_SECRET", "")

    # Lead Assignment
    DEFAULT_ASSIGNMENT_STRATEGY = os.getenv("DEFAULT_ASSIGNMENT_STRATEGY", "round_robin")

    # Redis (optional, for future use)
    REDIS_URL = os.getenv("REDIS_URL", None)

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_fields = {
            "ERPNEXT_BASE_URL": cls.ERPNEXT_BASE_URL,
            "ERPNEXT_API_KEY": cls.ERPNEXT_API_KEY,
            "ERPNEXT_API_SECRET": cls.ERPNEXT_API_SECRET,
        }

        missing = [
            field
            for field, value in required_fields.items()
            if not value or value.startswith("your_")
        ]

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please check your .env file."
            )


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True
    LOG_LEVEL = "DEBUG"

    # Use mock ERPNext for testing
    ERPNEXT_BASE_URL = "http://mock-erpnext.local"


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"


def get_config():
    """
    Return the appropriate configuration based on FLASK_ENV.

    Returns:
        Config: Configuration class for the current environment.
    """
    env = os.getenv("FLASK_ENV", "development").lower()

    if env == "testing":
        return TestingConfig
    elif env == "production":
        return ProductionConfig
    else:
        return DevelopmentConfig
