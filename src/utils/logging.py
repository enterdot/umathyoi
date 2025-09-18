"""Simple logging utility for development and debugging."""

import sys
from typing import Any


class Logger:
    """Simple logger for development and debugging."""
    
    DEBUG = True
    
    @classmethod
    def debug(cls, message: str, caller: Any | None = None, **kwargs: Any) -> None:
        """Log debug message if debug mode is enabled.
        
        Args:
            message: Debug message to log
            **kwargs: Additional context variables to include
        """
        if cls.DEBUG:
            context = f" ({', '.join(f'{k}={v}' for k, v in kwargs.items())})" if kwargs else ""
            print(f"[DEBUG] [{cls._get_caller_name(caller)}] {message}{context}", file=sys.stderr)
    
    @classmethod
    def info(cls, message: str, caller: Any | None = None) -> None:
        """Log info message.
        
        Args:
            message: Info message to log
        """
        print(f"[INFO] [{cls._get_caller_name(caller)}] {message}")
    
    @classmethod
    def warning(cls, message: str, caller: Any | None = None) -> None:
        """Log warning message.
        
        Args:
            message: Warning message to log
        """
        caller_name = caller.__class__.__name__ if caller else None
        print(f"[WARNING] [{self._get_caller_name(caller)}] {message}", file=sys.stderr)
    
    @classmethod
    def error(cls, message: str, caller: Any | None = None) -> None:
        """Log error message.
        
        Args:
            message: Error message to log
        """
        print(f"[ERROR] [{self._get_caller_name(caller)}] {message}", file=sys.stderr)
    
    @classmethod
    def _get_caller_name(cls, caller: Any | None) -> str:
        return caller.__class__.__name__ if caller else str(None)
