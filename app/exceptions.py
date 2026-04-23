"""Custom exception classes for the ERPNext CRM Integration service."""


class ValidationError(Exception):
    """Raised when incoming payload fails validation."""
    pass


class ERPNextError(Exception):
    """Raised when ERPNext API returns an error."""
    pass


class AssignmentError(Exception):
    """Raised when salesperson assignment fails."""
    pass


class TaskCreationError(Exception):
    """Raised when follow-up task creation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass
