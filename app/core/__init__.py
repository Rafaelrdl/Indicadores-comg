"""Core infrastructure package."""

from .config import get_settings
from .constants import *
from .exceptions import (
    APIError, 
    DataValidationError, 
    ApplicationError, 
    AppException,
    DataFetchError,
    ConfigurationError, 
    AuthenticationError, 
    CacheError,
    ValidationError,
    ErrorHandler,
    safe_operation
)

__all__ = [
    "get_settings",
    # Constants
    "OSType", "OSStatus", "EquipmentStatus", "UserRole",
    "COLORS", "API_ENDPOINTS",
    # Exceptions  
    "ApplicationError", "APIError", "DataValidationError", 
    "ConfigurationError", "AuthenticationError", "CacheError",
    # Legacy compatibility
    "settings", "AppException", "DataFetchError",
    "DEFAULT_PERIOD_MONTHS"
]

# Legacy compatibility
try:
    from .config import settings
except ImportError:
    settings = get_settings()
