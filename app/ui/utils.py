"""Utility functions for UI operations."""
from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Coroutine


def run_async_safe(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute async coroutine safely, handling event loop issues.
    
    This function handles the case where Streamlit might already have a running
    event loop, which would cause asyncio.run() to fail.
    """
    # For Streamlit, always use a new thread with a new event loop
    # to avoid conflicts with any existing loop
    def run_in_thread():
        new_loop = None
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        except Exception as e:
            # Log the error but don't crash
            print(f"Error in async execution: {e}")
            raise
        finally:
            # Safely close the loop
            if new_loop and not new_loop.is_closed():
                try:
                    new_loop.close()
                except Exception:
                    pass  # Ignore close errors
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()
