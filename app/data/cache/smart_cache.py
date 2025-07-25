"""Smart caching system for improved performance."""

from __future__ import annotations

import functools
import hashlib
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import streamlit as st

from ..core.constants import CACHE_TTL_DEFAULT

logger = logging.getLogger(__name__)
F = TypeVar('F', bound=Callable[..., Any])


class CacheManager:
    """Advanced cache management with intelligent key generation."""
    
    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """Generate a unique cache key from function arguments."""
        # Create a string representation of all arguments
        key_parts = []
        
        # Process positional arguments
        for arg in args:
            if hasattr(arg, '__dict__'):
                # For objects with attributes, use their dict representation
                key_parts.append(str(sorted(arg.__dict__.items())))
            else:
                key_parts.append(str(arg))
        
        # Process keyword arguments
        for key, value in sorted(kwargs.items()):
            if hasattr(value, '__dict__'):
                key_parts.append(f"{key}={str(sorted(value.__dict__.items()))}")
            else:
                key_parts.append(f"{key}={str(value)}")
        
        # Create hash of the combined key
        combined_key = "|".join(key_parts)
        return hashlib.md5(combined_key.encode()).hexdigest()
    
    @staticmethod
    def clear_cache_by_pattern(pattern: str) -> None:
        """Clear cache entries matching a pattern."""
        # Note: Streamlit doesn't provide pattern-based cache clearing
        # This is a placeholder for future implementation
        logger.info(f"Cache clear requested for pattern: {pattern}")


def smart_cache(
    ttl: int = CACHE_TTL_DEFAULT,
    key_func: Optional[Callable] = None,
    max_entries: Optional[int] = None,
    show_spinner: Union[bool, str] = True,
    persist: bool = False
) -> Callable[[F], F]:
    """
    Smart cache decorator with advanced features.
    
    Args:
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key
        max_entries: Maximum number of cache entries (not implemented in Streamlit)
        show_spinner: Show loading spinner (boolean or custom message)
        persist: Whether to persist cache across sessions
    
    Returns:
        Decorated function with caching
    """
    def decorator(func: F) -> F:
        # Determine spinner message
        if isinstance(show_spinner, str):
            spinner_msg = show_spinner
        elif show_spinner:
            spinner_msg = f"Loading {func.__name__}..."
        else:
            spinner_msg = None
        
        # Apply Streamlit cache with custom hash function if provided
        if key_func:
            @st.cache_data(
                ttl=ttl,
                show_spinner=spinner_msg,
                persist=persist,
                hash_funcs={type(key_func): lambda x: str(x)}
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate custom cache key
                cache_key = key_func(*args, **kwargs)
                logger.debug(f"Cache key for {func.__name__}: {cache_key}")
                return func(*args, **kwargs)
        else:
            @st.cache_data(
                ttl=ttl,
                show_spinner=spinner_msg,
                persist=persist
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def cache_with_filters(ttl: int = CACHE_TTL_DEFAULT) -> Callable[[F], F]:
    """
    Cache decorator optimized for functions that accept filter dictionaries.
    
    Args:
        ttl: Time to live in seconds
        
    Returns:
        Decorated function with filter-aware caching
    """
    def filter_key_func(*args, **kwargs):
        """Generate cache key based on filter parameters."""
        # Extract filters from arguments
        filters = None
        for arg in args:
            if isinstance(arg, dict) and any(
                key in arg for key in ['dt_ini', 'dt_fim', 'tipo_id', 'estado_ids']
            ):
                filters = arg
                break
        
        if 'filters' in kwargs:
            filters = kwargs['filters']
        
        if filters:
            # Create stable key from filter contents
            filter_items = sorted(filters.items()) if filters else []
            return f"filters_{hash(str(filter_items))}"
        
        return CacheManager.generate_cache_key(*args, **kwargs)
    
    return smart_cache(ttl=ttl, key_func=filter_key_func)


def invalidate_cache_on_error(func: F) -> F:
    """
    Decorator to invalidate cache when function raises an exception.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that clears its cache on error
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Clear the function's cache
            if hasattr(func, 'clear'):
                func.clear()
            logger.warning(f"Cache cleared for {func.__name__} due to error: {e}")
            raise
    
    return wrapper


# Convenience decorators for common cache patterns
def cache_os_data(ttl: int = CACHE_TTL_DEFAULT):
    """Cache decorator for Ordem de Serviço data."""
    return smart_cache(
        ttl=ttl,
        show_spinner="Carregando dados de ordens de serviço...",
        key_func=lambda *args, **kwargs: f"os_data_{CacheManager.generate_cache_key(*args, **kwargs)}"
    )


def cache_equipment_data(ttl: int = CACHE_TTL_DEFAULT):
    """Cache decorator for equipment data.""" 
    return smart_cache(
        ttl=ttl,
        show_spinner="Carregando dados de equipamentos...",
        key_func=lambda *args, **kwargs: f"equip_data_{CacheManager.generate_cache_key(*args, **kwargs)}"
    )


def cache_user_data(ttl: int = 86400):  # Daily cache for user data
    """Cache decorator for user/technician data."""
    return smart_cache(
        ttl=ttl,
        show_spinner="Carregando dados de usuários...",
        key_func=lambda *args, **kwargs: f"user_data_{CacheManager.generate_cache_key(*args, **kwargs)}"
    )
