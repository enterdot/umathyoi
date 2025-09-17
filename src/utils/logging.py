"""Simple logging utility for development and debugging."""

import sys
from typing import Any


class Logger:
    """Simple logger for development and debugging."""
    
    DEBUG = False  # Set to True for debug output
    
    @classmethod
    def debug(cls, message: str, **kwargs: Any) -> None:
        """Log debug message if debug mode is enabled.
        
        Args:
            message: Debug message to log
            **kwargs: Additional context variables to include
        """
        if cls.DEBUG:
            context = f" ({', '.join(f'{k}={v}' for k, v in kwargs.items())})" if kwargs else ""
            print(f"[DEBUG] {message}{context}", file=sys.stderr)
    
    @classmethod
    def info(cls, message: str) -> None:
        """Log info message.
        
        Args:
            message: Info message to log
        """
        print(f"[INFO] {message}")
    
    @classmethod
    def warning(cls, message: str) -> None:
        """Log warning message.
        
        Args:
            message: Warning message to log
        """
        print(f"[WARNING] {message}", file=sys.stderr)
    
    @classmethod
    def error(cls, message: str) -> None:
        """Log error message.
        
        Args:
            message: Error message to log
        """
        print(f"[ERROR] {message}", file=sys.stderr)
