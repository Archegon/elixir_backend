"""
Logging Demonstration for Elixir Backend

This script demonstrates how to use the centralized logging system
across different modules and scenarios.
"""

import os
import sys

# Add modules to path for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.logger import setup_logger, get_logger, ContextLogger, log_performance
from plc.plc import S7_200  # This will have logging built-in
import logging


def demonstrate_basic_logging():
    """Demonstrate basic logging functionality."""
    print("=" * 60)
    print("BASIC LOGGING DEMONSTRATION")
    print("=" * 60)
    
    # Create a logger for this demo
    logger = setup_logger("demo.basic", level=logging.INFO)
    
    logger.debug("This debug message won't appear (log level is INFO)")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


def demonstrate_context_logging():
    """Demonstrate context-aware logging."""
    print("\n" + "=" * 60)
    print("CONTEXT LOGGING DEMONSTRATION")
    print("=" * 60)
    
    logger = setup_logger("demo.context", level=logging.INFO)
    
    # Regular logging
    logger.info("Regular log message without context")
    
    # Context logging
    with ContextLogger(logger, user_id="USER123", session_id="SESSION456"):
        logger.info("This message includes context information")
        logger.warning("Warning with context")


def demonstrate_performance_logging():
    """Demonstrate performance monitoring with decorators."""
    print("\n" + "=" * 60)
    print("PERFORMANCE LOGGING DEMONSTRATION")
    print("=" * 60)
    
    logger = setup_logger("demo.performance", level=logging.INFO)
    
    @log_performance(logger, "data_processing")
    def slow_operation():
        """Simulate a slow operation."""
        import time
        time.sleep(1)  # Simulate processing time
        return "Processing complete"
    
    @log_performance(logger, "fast_calculation")
    def fast_operation():
        """Simulate a fast operation."""
        return sum(range(1000))
    
    # Run operations
    result1 = slow_operation()
    result2 = fast_operation()
    
    logger.info(f"Slow operation result: {result1}")
    logger.info(f"Fast operation result: {result2}")


def demonstrate_different_log_formats():
    """Demonstrate different logging formats."""
    print("\n" + "=" * 60)
    print("DIFFERENT LOG FORMATS DEMONSTRATION")
    print("=" * 60)
    
    # Default format
    logger_default = setup_logger("demo.format.default", format_style="default", log_to_file=False)
    logger_default.info("This uses the default format")
    
    # Detailed format
    logger_detailed = setup_logger("demo.format.detailed", format_style="detailed", log_to_file=False)
    logger_detailed.info("This uses the detailed format with function names")
    
    # Simple format
    logger_simple = setup_logger("demo.format.simple", format_style="simple", log_to_file=False)
    logger_simple.info("This uses the simple format")


def demonstrate_error_logging():
    """Demonstrate error logging with stack traces."""
    print("\n" + "=" * 60)
    print("ERROR LOGGING DEMONSTRATION")
    print("=" * 60)
    
    logger = setup_logger("demo.errors", level=logging.DEBUG)
    
    try:
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        logger.error(f"Division by zero error: {e}")
        logger.exception("Full exception with stack trace:")
    
    try:
        # Simulate another error
        data = {"key": "value"}
        value = data["nonexistent_key"]
    except KeyError as e:
        logger.error(f"Key error accessing data: {e}")


def demonstrate_plc_logging():
    """Demonstrate PLC logging (if PLC is available)."""
    print("\n" + "=" * 60)
    print("PLC LOGGING DEMONSTRATION")
    print("=" * 60)
    
    try:
        # This will demonstrate the logging built into the PLC class
        # Note: This will fail if no PLC is connected, but it will show the logging
        logger = setup_logger("demo.plc", level=logging.INFO)
        logger.info("Attempting to create PLC instance...")
        
        # Create PLC instance - this will trigger connection logging
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Try some operations (these will likely fail but show logging)
        try:
            value = plc.getMem("VX0.0")
            logger.info(f"Read value from VX0.0: {value}")
        except Exception as e:
            logger.info(f"PLC read failed (expected): {e}")
        
        try:
            plc.writeMem("VX0.1", True)
            logger.info("Successfully wrote to VX0.1")
        except Exception as e:
            logger.info(f"PLC write failed (expected): {e}")
        
        plc.disconnect()
        
    except Exception as e:
        logger = get_logger("demo.plc")
        logger.info(f"PLC demo failed (expected if no PLC connected): {e}")


def demonstrate_file_logging():
    """Demonstrate file logging capabilities."""
    print("\n" + "=" * 60)
    print("FILE LOGGING DEMONSTRATION")
    print("=" * 60)
    
    # Create logger that logs to both console and file
    logger = setup_logger("demo.file", level=logging.DEBUG, log_to_file=True)
    
    logger.info("This message will be logged to both console and file")
    logger.debug("This debug message will also be in the log file")
    logger.warning("Check the 'logs' directory for log files")
    
    # Create logger that only logs to file
    file_only_logger = setup_logger("demo.file_only", log_to_console=False, log_to_file=True)
    file_only_logger.info("This message only goes to the log file")
    
    print("Check the 'logs' directory to see the generated log files:")
    print("- logs/modules_logger_demo_file.log")
    print("- logs/modules_logger_demo_file_only.log")


if __name__ == "__main__":
    print("ELIXIR BACKEND LOGGING SYSTEM DEMONSTRATION")
    print("This demo shows various logging capabilities.")
    print("Log files will be created in the 'logs' directory.")
    
    # Run demonstrations
    demonstrate_basic_logging()
    demonstrate_context_logging()
    demonstrate_performance_logging()
    demonstrate_different_log_formats()
    demonstrate_error_logging()
    demonstrate_file_logging()
    demonstrate_plc_logging()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("Check the 'logs' directory for generated log files.")
    print("You can configure logging via environment variables:")
    print("- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    print("- LOG_DIR: Directory for log files")
    print("- Other configuration options in modules/logger.py") 