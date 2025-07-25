"""Cache management utilities and initialization."""

from .smart_cache import (
    CacheManager,
    smart_cache,
    cache_with_filters,
    invalidate_cache_on_error,
    cache_os_data,
    cache_equipment_data,
    cache_user_data,
)

__all__ = [
    "CacheManager",
    "smart_cache",
    "cache_with_filters", 
    "invalidate_cache_on_error",
    "cache_os_data",
    "cache_equipment_data",
    "cache_user_data",
]
