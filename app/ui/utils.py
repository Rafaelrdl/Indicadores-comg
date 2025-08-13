"""Utility functions for UI operations."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any


def run_async_safe(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute async coroutine safely, handling event loop issues.
    
    This function handles the case where Streamlit might already have a running
    event loop, which would cause asyncio.run() to fail.
    
    Fixed version that properly handles Streamlit context to avoid
    'missing ScriptRunContext' warnings.
    """
    try:
        # Try to run in the current event loop if it exists
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in a running loop, need to use a thread
            import threading

            from streamlit.runtime.scriptrunner import get_script_run_ctx

            # Capture current Streamlit context
            ctx = get_script_run_ctx()
            result = None
            exception = None

            def run_in_thread():
                nonlocal result, exception
                new_loop = None
                try:
                    # Set up new event loop in thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)

                    # Run the coroutine
                    result = new_loop.run_until_complete(coro)

                except Exception as e:
                    exception = e
                finally:
                    # Clean up the loop
                    if new_loop and not new_loop.is_closed():
                        try:
                            new_loop.close()
                        except Exception:
                            pass

            # Run in thread without ThreadPoolExecutor to avoid context issues
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if exception:
                raise exception
            return result

        else:
            # No running loop, can use asyncio.run directly
            return asyncio.run(coro)

    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)
