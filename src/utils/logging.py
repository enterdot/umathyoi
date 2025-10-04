"""Standard Python logging setup for the application."""

import logging
import sys

def setup_logging(level: str = "debug") -> None:
    """Set up application-wide logging configuration.

    Args:
        level: Logging level ("debug", "info", "warning", "error")
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter('[%(levelname)s] [%(name)s] %(message)s')
    
    # Console handler for all levels
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
