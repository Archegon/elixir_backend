"""
Centralized logging configuration for the Elixir Backend application.

This module provides a standardized logging setup that can be used across
all modules and classes in the application.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """Configuration class for application logging."""
    
    # Default log format
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d:%(funcName)s] - %(message)s"
    SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Default log level
    DEFAULT_LEVEL = logging.INFO
    
    # Default log directory
    DEFAULT_LOG_DIR = "logs"
    
    # Maximum log file size (10MB)
    MAX_LOG_SIZE = 10 * 1024 * 1024
    
    # Number of backup log files to keep
    BACKUP_COUNT = 5


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: Optional[str] = None,
    format_style: str = "default"
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_dir: Directory to store log files
        format_style: Format style ('default', 'detailed', 'simple')
    
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Set level from environment variable or parameter or default
    if level is None:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, LoggerConfig.DEFAULT_LEVEL)
    
    logger.setLevel(level)
    
    # Choose format
    format_map = {
        "default": LoggerConfig.DEFAULT_FORMAT,
        "detailed": LoggerConfig.DETAILED_FORMAT,
        "simple": LoggerConfig.SIMPLE_FORMAT
    }
    log_format = format_map.get(format_style, LoggerConfig.DEFAULT_FORMAT)
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_dir = log_dir or LoggerConfig.DEFAULT_LOG_DIR
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(exist_ok=True)
        
        # Create log file path
        log_file = log_dir_path / f"{name.replace('.', '_')}.log"
        
        # Rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LoggerConfig.MAX_LOG_SIZE,
            backupCount=LoggerConfig.BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. If it doesn't exist, create it with default settings.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class ContextLogger:
    """
    Context manager for adding context to log messages.
    
    Example:
        with ContextLogger(logger, operation="PLC_READ", address="VX0.0"):
            logger.info("Starting operation")  # Will include context
    """
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_performance(logger: logging.Logger, operation: str):
    """
    Decorator to log performance metrics for functions.
    
    Args:
        logger: Logger instance to use
        operation: Name of the operation being timed
    
    Example:
        @log_performance(logger, "memory_read")
        def read_memory(self, address):
            # function implementation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"{operation} completed successfully in {duration:.3f}s")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"{operation} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


def configure_root_logger():
    """Configure the root logger for the application."""
    logging.basicConfig(
        level=logging.WARNING,  # Only show warnings and errors from third-party libraries
        format=LoggerConfig.SIMPLE_FORMAT
    )


# Initialize logging when module is imported
configure_root_logger() 