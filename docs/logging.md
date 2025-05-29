# Logging System Documentation

## Overview

The Elixir Backend project includes a comprehensive, centralized logging system that provides consistent logging across all modules and classes. The system supports multiple log levels, formats, and output destinations.

## Features

- **Centralized Configuration**: Single point of configuration for all logging
- **Multiple Output Destinations**: Console and file logging with rotating files
- **Configurable Formats**: Default, detailed, and simple formatting options
- **Performance Monitoring**: Built-in decorators for timing operations
- **Context Logging**: Add contextual information to log messages
- **Environment-based Configuration**: Configure via environment variables
- **Thread-safe**: Safe for multi-threaded applications

## Quick Start

### Basic Usage

```python
from modules.logger import setup_logger

# Create a logger
logger = setup_logger("my_module")

# Log messages
logger.info("Application started")
logger.warning("This is a warning")
logger.error("An error occurred")
```

### Using in Classes

```python
from modules.logger import setup_logger

class MyClass:
    def __init__(self):
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Class initialized")
    
    def do_something(self):
        self.logger.debug("Starting operation")
        # ... do work ...
        self.logger.info("Operation completed")
```

## Configuration

### Environment Variables

Set these environment variables to configure logging:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log directory
LOG_DIR=logs

# Enable/disable file logging
LOG_TO_FILE=true

# Enable/disable console logging  
LOG_TO_CONSOLE=true

# Log format style
LOG_FORMAT_STYLE=default
```

### Programmatic Configuration

```python
from modules.logger import setup_logger
import logging

# Create logger with specific settings
logger = setup_logger(
    name="my_app",
    level=logging.DEBUG,
    log_to_file=True,
    log_to_console=True,
    log_dir="custom_logs",
    format_style="detailed"
)
```

## Log Formats

### Default Format
```
2024-01-15 10:30:15,123 - my_module - INFO - [module.py:42] - Message text
```

### Detailed Format
```
2024-01-15 10:30:15,123 - my_module - INFO - [module.py:42:function_name] - Message text
```

### Simple Format
```
2024-01-15 10:30:15,123 - INFO - Message text
```

## Advanced Features

### Performance Monitoring

Use the `@log_performance` decorator to automatically log execution time:

```python
from modules.logger import setup_logger, log_performance

logger = setup_logger("performance_demo")

@log_performance(logger, "database_query")
def query_database():
    # ... database operation ...
    return results

# This will log: "database_query completed successfully in 0.123s"
result = query_database()
```

### Context Logging

Add contextual information to log messages:

```python
from modules.logger import setup_logger, ContextLogger

logger = setup_logger("context_demo")

with ContextLogger(logger, user_id="USER123", operation="data_processing"):
    logger.info("Processing started")  # Will include context
    logger.error("Processing failed")  # Will include context
```

### Error Logging with Stack Traces

```python
try:
    # ... some operation ...
    pass
except Exception as e:
    logger.error(f"Operation failed: {e}")
    logger.exception("Full stack trace:")  # Includes full traceback
```

## File Management

- Log files are automatically created in the specified directory
- Files use rotating handlers (max 10MB per file, 5 backup files)
- Log file names follow the pattern: `module_name.log`
- Old log files are automatically compressed and archived

## Integration Examples

### PLC Class Integration

The PLC class includes comprehensive logging:

```python
from modules.plc import S7_200

# PLC operations are automatically logged
plc = S7_200(ip="192.168.1.100")  # Logs connection attempt
value = plc.getMem("VX0.0")       # Logs read operation with timing
plc.writeMem("VX0.1", True)       # Logs write operation with timing
plc.disconnect()                  # Logs disconnection
```

### API Integration

For FastAPI applications:

```python
from modules.logger import setup_logger
from fastapi import FastAPI

app = FastAPI()
logger = setup_logger("api")

@app.get("/data")
async def get_data():
    logger.info("API endpoint called: /data")
    try:
        # ... process request ...
        logger.info("Data retrieved successfully")
        return {"data": "value"}
    except Exception as e:
        logger.error(f"API error: {e}")
        raise
```

## Best Practices

### 1. Logger Naming
Use hierarchical names for better organization:
```python
# Good
logger = setup_logger("myapp.database.connection")
logger = setup_logger("myapp.api.auth")

# Avoid
logger = setup_logger("logger1")
```

### 2. Log Levels
Use appropriate log levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened, but program continues
- **ERROR**: A serious problem occurred
- **CRITICAL**: Program may not be able to continue

### 3. Message Format
Write clear, actionable log messages:
```python
# Good
logger.error(f"Failed to connect to database at {host}:{port} - {error}")

# Avoid
logger.error("Error")
```

### 4. Sensitive Information
Never log sensitive data:
```python
# Good
logger.info(f"User {user_id} logged in")

# Avoid
logger.info(f"User {username} logged in with password {password}")
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the application has write permissions to the log directory
2. **Missing Log Files**: Check that `LOG_TO_FILE` is set to `true` and log directory exists
3. **Duplicate Messages**: Ensure you're not creating multiple loggers with the same name

### Debug Logging

To enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
```

Or programmatically:

```python
import logging
logger = setup_logger("debug", level=logging.DEBUG)
```

## Performance Considerations

- File logging has minimal performance impact due to buffering
- Rotating file handlers prevent disk space issues
- Log level filtering happens early to minimize processing overhead
- Context logging adds minimal overhead

## Example Configuration Files

### .env file
```bash
# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
LOG_FORMAT_STYLE=default
```

### Production Configuration
For production environments, consider:
- Setting `LOG_LEVEL=WARNING` or `LOG_LEVEL=ERROR`
- Increasing `MAX_LOG_SIZE` in `LoggerConfig`
- Using external log aggregation services
- Implementing log rotation policies

## Running the Demo

To see the logging system in action:

```bash
cd examples
python logging_demo.py
```

This will demonstrate all logging features and create sample log files in the `logs` directory. 