"""Custom decorators for the application."""

from gi.repository import GLib
from functools import lru_cache, wraps
import inspect
import logging
import time
from typing import Callable


def debounce(wait_ms: int = 500):
    """Debounce decorator - waits for activity to stop."""
    
    def decorator(func):
        pending_timer = None
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal pending_timer
            
            if pending_timer is not None:
                GLib.source_remove(pending_timer)
            
            def timer_expired():
                nonlocal pending_timer
                pending_timer = None
                func(*args, **kwargs)
                return False
            
            pending_timer = GLib.timeout_add(wait_ms, timer_expired)
        
        return wrapper
    return decorator

def stopwatch(log_func: Callable[[str], None] = None, show_args=False):
    """
    Stopwatch decorator - logs execution time.
    
    Args:
        log_func: Function to call with timing message.
                  Examples: print, logger.debug, logger.info
    """
    def decorator(func):
        nonlocal log_func
        if log_func is None:
            # Default to module logger's debug
            module_logger = logging.getLogger(func.__module__)
            log_func = module_logger.debug
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            
            if show_args:
                args_repr = ', '.join(repr(a) for a in args)
                kwargs_repr = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
                all_args = ', '.join(filter(None, [args_repr, kwargs_repr]))
                log_func(f"{func.__name__}({all_args}) took {elapsed*1000:.2f}ms")
            else:
                log_func(f"{func.__name__} took {elapsed*1000:.2f}ms")
            
            return result


        
        return wrapper
    return decorator


def throttle(wait_ms: int = 500):
    """Throttle decorator - limits execution rate."""
    
    def decorator(func):
        last_run_time = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_run_time
            
            current_time = GLib.get_monotonic_time() / 1000
            logger = logging.getLogger("THROTTLE_TEST")
            logger.debug(f"{last_run_time=}, {current_time=}")
            
            if current_time - last_run_time >= wait_ms:
                last_run_time = current_time
                func(*args, **kwargs)
        
        return wrapper
    return decorator


def memoize(maxsize=128):
    """
    Universal memoize decorator for functions and methods.
    Automatically detects instance methods and prevents memory leaks.
    """
    def decorator(func):
        sig = inspect.signature(func)
        is_method = 'self' in sig.parameters
        
        if is_method:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                cache_name = f'_cache_{func.__name__}'
                
                if not hasattr(self, cache_name):
                    cached_func = lru_cache(maxsize=maxsize)(
                        lambda *a, **kw: func(self, *a, **kw)
                    )
                    setattr(self, cache_name, cached_func)
                
                return getattr(self, cache_name)(*args, **kwargs)
            
            return wrapper
        else:
            return lru_cache(maxsize=maxsize)(func)
    
    return decorator
