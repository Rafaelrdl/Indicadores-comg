"""Core infrastructure package."""

from .config import get_settings
from .constants import *
from .exceptions import *

__all__ = [
    "get_settings",
    # Constants
    "OSType", "OSStatus", "EquipmentStatus", "UserRole",
    "COLORS", "CACHE_TTL", "API_ENDPOINTS",
    # Exceptions  
    "ApplicationError", "APIError", "DataValidationError", 
    "ConfigurationError", "AuthenticationError", "CacheError",
    # Legacy compatibility
    "settings", "AppException", "DataFetchError",
    "CACHE_TTL_DEFAULT", "CACHE_TTL_HEAVY", "DEFAULT_PERIOD_MONTHS"
]

# Legacy compatibility
try:
    from .config import settings
except ImportError:
    settings = get_settings()
